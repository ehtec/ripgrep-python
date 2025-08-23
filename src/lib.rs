use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::path::PathBuf;
use std::collections::HashSet;
use ignore::WalkBuilder;
use grep_searcher::{Searcher, sinks};
use grep_regex::{RegexMatcher, RegexMatcherBuilder};
use std::fs::File;
use globset::Glob;

/// Output modes for search results
#[derive(Debug, Clone, PartialEq)]
pub enum OutputMode {
    Content,
    FilesWithMatches,
    Count,
}

impl OutputMode {
    fn from_str(s: &str) -> PyResult<Self> {
        match s {
            "content" => Ok(OutputMode::Content),
            "files_with_matches" => Ok(OutputMode::FilesWithMatches),
            "count" => Ok(OutputMode::Count),
            _ => Err(PyValueError::new_err(format!("Invalid output mode: {}", s))),
        }
    }
}

/// Search result for content mode
#[derive(Debug, Clone)]
pub struct ContentResult {
    pub path: String,
    pub line_number: u64,
    pub content: String,
    pub before_context: Vec<String>,
    pub after_context: Vec<String>,
}

/// Search result for count mode
#[derive(Debug, Clone)]
pub struct CountResult {
    pub path: String,
    pub count: u64,
}

/// Main Grep interface that provides ripgrep-like functionality
#[pyclass(module = "pyripgrep")]
pub struct Grep {}

#[pymethods]
impl Grep {
    #[new]
    fn new() -> Self {
        Grep {}
    }

    /// Main search method with ripgrep-like interface
    /// Supports the exact parameter names as required by the Grep tool specification
    #[pyo3(signature = (
        pattern,
        path = None,
        glob = None,
        output_mode = None,
        B = None,      // -B flag: lines before
        A = None,      // -A flag: lines after
        C = None,      // -C flag: lines before and after
        n = None,      // -n flag: show line numbers
        i = None,      // -i flag: case insensitive
        r#type = None, // type parameter: file type filter
        head_limit = None,
        multiline = None
    ))]
    fn search(
        &self,
        py: Python,
        pattern: &str,
        path: Option<&str>,
        glob: Option<&str>,
        output_mode: Option<&str>,
        B: Option<u64>,           // -B: lines before match
        A: Option<u64>,           // -A: lines after match
        C: Option<u64>,           // -C: lines before and after match
        n: Option<bool>,          // -n: show line numbers
        i: Option<bool>,          // -i: case insensitive
        r#type: Option<&str>,     // type: file type filter
        head_limit: Option<usize>,
        multiline: Option<bool>,
    ) -> PyResult<PyObject> {
        let output_mode = OutputMode::from_str(output_mode.unwrap_or("files_with_matches"))?;
        let path = path.unwrap_or(".");
        let case_insensitive = i.unwrap_or(false);
        let multiline = multiline.unwrap_or(false);
        let line_numbers = n.unwrap_or(false);

        // Handle context options - C overrides A and B
        let (before_ctx, after_ctx) = if let Some(c) = C {
            (c, c)
        } else {
            (B.unwrap_or(0), A.unwrap_or(0))
        };

        // Build matcher
        let matcher = self.build_matcher(pattern, case_insensitive, multiline)?;

        // Search based on output mode
        match output_mode {
            OutputMode::Content => {
                let results = self.search_content(
                    &matcher,
                    path,
                    glob,
                    r#type,
                    before_ctx,
                    after_ctx,
                    line_numbers,
                    head_limit,
                )?;
                Ok(self.format_content_results(py, results, line_numbers)?)
            }
            OutputMode::FilesWithMatches => {
                let files = self.search_files(&matcher, path, glob, r#type, head_limit)?;
                Ok(files.into_py(py))
            }
            OutputMode::Count => {
                let counts = self.search_count(&matcher, path, glob, r#type, head_limit)?;
                Ok(self.format_count_results(py, counts)?)
            }
        }
    }
}

impl Grep {
    /// Build regex matcher based on options
    fn build_matcher(
        &self,
        pattern: &str,
        case_insensitive: bool,
        multiline: bool,
    ) -> PyResult<RegexMatcher> {
        let mut builder = RegexMatcherBuilder::new();

        if case_insensitive {
            builder.case_insensitive(true);
        }

        if multiline {
            builder.multi_line(true).dot_matches_new_line(true);
        }

        builder
            .build(pattern)
            .map_err(|e| PyValueError::new_err(format!("Invalid pattern: {}", e)))
    }

    /// Search for content with context
    fn search_content(
        &self,
        matcher: &RegexMatcher,
        path: &str,
        glob: Option<&str>,
        file_type: Option<&str>,
        before_context: u64,
        after_context: u64,
        _line_numbers: bool,
        head_limit: Option<usize>,
    ) -> PyResult<Vec<ContentResult>> {
        let mut results = Vec::new();
        let mut result_count = 0;

        let walker = self.build_walker(path, glob, file_type)?;

        for entry in walker {
            if let Some(limit) = head_limit {
                if result_count >= limit {
                    break;
                }
            }

            let entry = entry.map_err(|e| PyValueError::new_err(format!("Walk error: {}", e)))?;

            if !entry.file_type().map_or(false, |ft| ft.is_file()) {
                continue;
            }

            // Apply file type filter
            if let Some(ftype) = file_type {
                if !self.matches_file_type(entry.path(), ftype) {
                    continue;
                }
            }

            // Apply glob filter
            if let Some(glob_pattern) = glob {
                if !self.matches_glob(entry.path(), glob_pattern) {
                    continue;
                }
            }

            let before_count = results.len();
            self.search_file_content(
                matcher,
                entry.path(),
                before_context,
                after_context,
                &mut results,
            )?;

            // Count actual new results for head_limit
            if results.len() > before_count {
                result_count += results.len() - before_count;
            }
        }

        // Apply head limit to results
        if let Some(limit) = head_limit {
            results.truncate(limit);
        }

        Ok(results)
    }

    /// Search for files containing matches
    fn search_files(
        &self,
        matcher: &RegexMatcher,
        path: &str,
        glob: Option<&str>,
        file_type: Option<&str>,
        head_limit: Option<usize>,
    ) -> PyResult<Vec<String>> {
        let mut files = HashSet::new();
        let walker = self.build_walker(path, glob, file_type)?;

        for entry in walker {
            if let Some(limit) = head_limit {
                if files.len() >= limit {
                    break;
                }
            }

            let entry = entry.map_err(|e| PyValueError::new_err(format!("Walk error: {}", e)))?;

            if !entry.file_type().map_or(false, |ft| ft.is_file()) {
                continue;
            }

            // Apply file type filter
            if let Some(ftype) = file_type {
                if !self.matches_file_type(entry.path(), ftype) {
                    continue;
                }
            }

            // Apply glob filter
            if let Some(glob_pattern) = glob {
                if !self.matches_glob(entry.path(), glob_pattern) {
                    continue;
                }
            }

            if self.file_has_match(matcher, entry.path())? {
                files.insert(entry.path().to_string_lossy().to_string());
            }
        }

        Ok(files.into_iter().collect())
    }

    /// Search and count matches per file
    fn search_count(
        &self,
        matcher: &RegexMatcher,
        path: &str,
        glob: Option<&str>,
        file_type: Option<&str>,
        head_limit: Option<usize>,
    ) -> PyResult<Vec<CountResult>> {
        let mut counts = Vec::new();
        let walker = self.build_walker(path, glob, file_type)?;

        for entry in walker {
            if let Some(limit) = head_limit {
                if counts.len() >= limit {
                    break;
                }
            }

            let entry = entry.map_err(|e| PyValueError::new_err(format!("Walk error: {}", e)))?;

            if !entry.file_type().map_or(false, |ft| ft.is_file()) {
                continue;
            }

            // Apply file type filter
            if let Some(ftype) = file_type {
                if !self.matches_file_type(entry.path(), ftype) {
                    continue;
                }
            }

            // Apply glob filter
            if let Some(glob_pattern) = glob {
                if !self.matches_glob(entry.path(), glob_pattern) {
                    continue;
                }
            }

            let count = self.count_matches_in_file(matcher, entry.path())?;
            if count > 0 {
                counts.push(CountResult {
                    path: entry.path().to_string_lossy().to_string(),
                    count,
                });
            }
        }

        Ok(counts)
    }

    /// Build directory walker with filtering options
    fn build_walker(
        &self,
        path: &str,
        glob: Option<&str>,
        file_type: Option<&str>,
    ) -> PyResult<ignore::Walk> {
        let path_buf = PathBuf::from(path);
        if !path_buf.exists() {
            return Err(PyValueError::new_err(format!("Path not found: {}", path)));
        }

        let mut builder = WalkBuilder::new(&path_buf);
        builder
            .hidden(false)
            .git_ignore(true)
            .git_global(true)
            .parents(true)
            .follow_links(false);

        // Add glob pattern if provided
        if let Some(glob_pattern) = glob {
            builder.add_custom_ignore_filename(glob_pattern);
        }

        // Add file type filtering
        if let Some(ftype) = file_type {
            self.add_file_type_filter(&mut builder, ftype)?;
        }

        Ok(builder.build())
    }

    /// Add file type filtering to walker
    fn add_file_type_filter(
        &self,
        builder: &mut WalkBuilder,
        file_type: &str,
    ) -> PyResult<()> {
        // Simple file type mapping - extend as needed
        let extensions = match file_type {
            "rs" | "rust" => vec!["rs"],
            "py" | "python" => vec!["py", "pyw", "pyi"],
            "js" | "javascript" => vec!["js", "jsx"],
            "ts" | "typescript" => vec!["ts", "tsx"],
            "java" => vec!["java"],
            "c" => vec!["c", "h"],
            "cpp" | "c++" => vec!["cpp", "cxx", "cc", "hpp", "hxx"],
            "go" => vec!["go"],
            "rb" | "ruby" => vec!["rb"],
            "php" => vec!["php"],
            "md" | "markdown" => vec!["md", "markdown"],
            "txt" | "text" => vec!["txt"],
            "json" => vec!["json"],
            "xml" => vec!["xml"],
            "yaml" | "yml" => vec!["yaml", "yml"],
            "toml" => vec!["toml"],
            _ => return Err(PyValueError::new_err(format!("Unknown file type: {}", file_type))),
        };

        // Note: WalkBuilder doesn't have a direct extension filter,
        // so we'll implement this in the search methods by checking extensions
        Ok(())
    }

    /// Check if file matches the given file type
    fn matches_file_type(&self, path: &std::path::Path, file_type: &str) -> bool {
        let extensions = match file_type {
            "rs" | "rust" => vec!["rs"],
            "py" | "python" => vec!["py", "pyw", "pyi"],
            "js" | "javascript" => vec!["js", "jsx"],
            "ts" | "typescript" => vec!["ts", "tsx"],
            "java" => vec!["java"],
            "c" => vec!["c", "h"],
            "cpp" | "c++" => vec!["cpp", "cxx", "cc", "hpp", "hxx"],
            "go" => vec!["go"],
            "rb" | "ruby" => vec!["rb"],
            "php" => vec!["php"],
            "md" | "markdown" => vec!["md", "markdown"],
            "txt" | "text" => vec!["txt"],
            "json" => vec!["json"],
            "xml" => vec!["xml"],
            "yaml" | "yml" => vec!["yaml", "yml"],
            "toml" => vec!["toml"],
            _ => return false,
        };

        if let Some(ext) = path.extension() {
            if let Some(ext_str) = ext.to_str() {
                return extensions.iter().any(|&e| e == ext_str);
            }
        }
        false
    }

    /// Check if file matches the given glob pattern
    fn matches_glob(&self, path: &std::path::Path, pattern: &str) -> bool {
        match Glob::new(pattern) {
            Ok(glob) => {
                let matcher = glob.compile_matcher();
                
                // Try matching against the full path
                if matcher.is_match(path) {
                    return true;
                }
                
                // Try matching against just the filename
                if let Some(filename) = path.file_name() {
                    return matcher.is_match(filename);
                }
                
                false
            }
            Err(_) => false, // Invalid pattern
        }
    }

    /// Search a single file for content with context
    fn search_file_content(
        &self,
        matcher: &RegexMatcher,
        path: &std::path::Path,
        before_context: u64,
        after_context: u64,
        results: &mut Vec<ContentResult>,
    ) -> PyResult<()> {
        use std::io::{BufRead, BufReader};
        
        let file = File::open(path)
            .map_err(|e| PyValueError::new_err(format!("Cannot open file {}: {}", path.display(), e)))?;

        let path_str = path.to_string_lossy().to_string();
        let reader = BufReader::new(file);
        let lines: Result<Vec<String>, _> = reader.lines().collect();
        
        let lines = match lines {
            Ok(lines) => lines,
            Err(_) => return Ok(()), // Skip problematic files silently
        };

        let mut searcher = Searcher::new();
        
        // Find all matching line numbers first
        let mut matching_lines = Vec::new();
        for (line_idx, line) in lines.iter().enumerate() {
            let line_num = (line_idx + 1) as u64;
            if matcher.is_match(line.as_bytes()).unwrap_or(false) {
                matching_lines.push(line_num);
            }
        }

        // For each match, collect context and create result
        for &match_line in &matching_lines {
            let match_idx = (match_line - 1) as usize;
            
            // Collect before context
            let before_start = if before_context == 0 {
                match_idx
            } else {
                match_idx.saturating_sub(before_context as usize)
            };
            
            let mut before_ctx = Vec::new();
            if before_context > 0 {
                for i in before_start..match_idx {
                    if i < lines.len() {
                        before_ctx.push(lines[i].clone());
                    }
                }
            }

            // Collect after context
            let mut after_ctx = Vec::new();
            if after_context > 0 {
                let after_end = std::cmp::min(lines.len(), match_idx + 1 + after_context as usize);
                for i in (match_idx + 1)..after_end {
                    after_ctx.push(lines[i].clone());
                }
            }

            results.push(ContentResult {
                path: path_str.clone(),
                line_number: match_line,
                content: lines[match_idx].clone(),
                before_context: before_ctx,
                after_context: after_ctx,
            });
        }

        Ok(())
    }

    /// Check if file has any matches
    fn file_has_match(&self, matcher: &RegexMatcher, path: &std::path::Path) -> PyResult<bool> {
        let file = File::open(path).map_err(|e| {
            PyValueError::new_err(format!("Cannot open file {}: {}", path.display(), e))
        })?;

        let mut searcher = Searcher::new();
        let mut has_match = false;

        let result = searcher.search_file(matcher, &file, sinks::UTF8(|_lnum, _line| {
            has_match = true;
            Ok(false) // Stop after first match
        }));

        // If the search failed (e.g., binary file), just return false
        match result {
            Ok(_) => Ok(has_match),
            Err(_) => Ok(false), // Skip problematic files
        }
    }

    /// Count matches in a file
    fn count_matches_in_file(&self, matcher: &RegexMatcher, path: &std::path::Path) -> PyResult<u64> {
        let file = File::open(path).map_err(|e| {
            PyValueError::new_err(format!("Cannot open file {}: {}", path.display(), e))
        })?;

        let mut searcher = Searcher::new();
        let mut count = 0u64;

        let result = searcher.search_file(matcher, &file, sinks::UTF8(|_lnum, _line| {
            count += 1;
            Ok(true)
        }));

        match result {
            Ok(_) => Ok(count),
            Err(_) => Ok(0), // Skip problematic files
        }
    }

    /// Format content results for Python
    fn format_content_results(
        &self,
        py: Python,
        results: Vec<ContentResult>,
        show_line_numbers: bool,
    ) -> PyResult<PyObject> {
        let mut py_results = Vec::new();
        
        for r in results {
            // Add before context lines
            for (i, before_line) in r.before_context.iter().enumerate() {
                let context_line_num = if show_line_numbers {
                    r.line_number - (r.before_context.len() as u64) + (i as u64)
                } else {
                    0 // Not used when line numbers are off
                };
                
                let formatted_line = if show_line_numbers {
                    format!("{}:{}:{}", r.path, context_line_num, before_line)
                } else {
                    format!("{}:{}", r.path, before_line)
                };
                py_results.push(formatted_line);
            }
            
            // Add the match line
            let main_line = if show_line_numbers {
                format!("{}:{}:{}", r.path, r.line_number, r.content)
            } else {
                format!("{}:{}", r.path, r.content)
            };
            py_results.push(main_line);
            
            // Add after context lines
            for (i, after_line) in r.after_context.iter().enumerate() {
                let context_line_num = if show_line_numbers {
                    r.line_number + 1 + (i as u64)
                } else {
                    0 // Not used when line numbers are off
                };
                
                let formatted_line = if show_line_numbers {
                    format!("{}:{}:{}", r.path, context_line_num, after_line)
                } else {
                    format!("{}:{}", r.path, after_line)
                };
                py_results.push(formatted_line);
            }
        }

        Ok(py_results.into_py(py))
    }

    /// Format count results for Python
    fn format_count_results(&self, py: Python, counts: Vec<CountResult>) -> PyResult<PyObject> {
        let dict = PyDict::new(py);
        for count in counts {
            dict.set_item(&count.path, count.count)?;
        }
        Ok(dict.into_py(py))
    }
}

/// Python module definition
#[pymodule]
fn pyripgrep(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Grep>()?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
