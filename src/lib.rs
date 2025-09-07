use pyo3::exceptions::{PyValueError, PyTimeoutError};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString};
use std::path::{Path, PathBuf};
use std::collections::{HashSet, HashMap};
use ignore::{WalkBuilder, types::TypesBuilder, overrides::OverrideBuilder};
use grep_searcher::{Searcher, sinks};
use grep_regex::{RegexMatcher, RegexMatcherBuilder};
use grep_matcher::Matcher;
use std::fs::File;
use std::time::{Duration, Instant};
use std::io;

/// --- Pure-Rust error used while GIL is released ---
#[derive(Debug)]
enum RGErr {
    Walk(ignore::Error),
    Io(io::Error),
    Timeout,
}

fn to_pyerr(e: RGErr) -> PyErr {
    match e {
        RGErr::Timeout => PyTimeoutError::new_err("search timed out"),
        RGErr::Walk(err) => PyValueError::new_err(format!("Walk error: {}", err)),
        RGErr::Io(err) => PyValueError::new_err(format!("IO error: {}", err)),
    }
}


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

/// Timeout helper functions
#[inline]
fn deadline_from_secs(timeout: Option<f64>) -> Option<Instant> {
    timeout.map(|t| Instant::now() + Duration::from_secs_f64(t.max(0.0)))
}

#[inline]
fn timed_out(deadline: Option<Instant>) -> bool {
    match deadline {
        Some(d) => Instant::now() >= d,
        None => false,
    }
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
        multiline = None,
        timeout = None // timeout in seconds
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
        r#type: Option<&PyAny>,   // type: file type filter (string or list)
        head_limit: Option<usize>,
        multiline: Option<bool>,
        timeout: Option<f64>,     // timeout in seconds
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

        // Parse types outside allow_threads (can raise Python exceptions here)
        let parsed_types = Self::parse_types(r#type)?;

        // Build matcher
        let matcher = self.build_matcher(pattern, case_insensitive, multiline)?;

        // Compute deadline from timeout
        let deadline = deadline_from_secs(timeout);

        // Build walker outside allow_threads (can raise Python exceptions here)
        let (walker, type_matcher) = self.build_walker(path, glob, &parsed_types)?;

        // Search based on output mode (heavy part runs without the GIL)
        match output_mode {
            OutputMode::Content => {
                let results = py.allow_threads(|| {
                    self.search_content_inner(
                        &matcher,
                        walker,
                        type_matcher.as_ref(),
                        before_ctx,
                        after_ctx,
                        deadline,
                    )
                }).map_err(to_pyerr)?;
                Ok(self.format_content_results(py, results, line_numbers, head_limit)?)
            }
            OutputMode::FilesWithMatches => {
                let files = py.allow_threads(|| {
                    self.search_files_inner(&matcher, walker, type_matcher.as_ref(), head_limit, deadline)
                }).map_err(to_pyerr)?;
                Ok(files.into_py(py))
            }
            OutputMode::Count => {
                let counts = py.allow_threads(|| {
                    self.search_count_inner(&matcher, walker, type_matcher.as_ref(), head_limit, deadline)
                }).map_err(to_pyerr)?;
                Ok(self.format_count_results(py, counts)?)
            }
        }
    }
}

impl Grep {
    /// Create mapping from custom type names to official ripgrep type names
    fn create_type_mapping() -> HashMap<&'static str, &'static str> {
        let mut map = HashMap::new();
        
        // Map custom names to official ripgrep type names
        map.insert("python", "py");
        map.insert("javascript", "js");
        map.insert("rust", "rust");  // already matches
        map.insert("typescript", "ts");
        map.insert("markdown", "md");
        map.insert("c++", "cpp");
        map.insert("ruby", "rb");
        
        // Official names map to themselves
        map.insert("py", "py");
        map.insert("js", "js");  
        map.insert("ts", "ts");
        map.insert("rs", "rust");  // rs -> rust for ripgrep
        map.insert("cpp", "cpp");
        map.insert("c", "c");
        map.insert("go", "go");
        map.insert("java", "java");
        map.insert("php", "php");
        map.insert("rb", "rb");
        map.insert("md", "md");
        map.insert("txt", "txt");
        map.insert("json", "json");
        map.insert("xml", "xml");
        map.insert("yaml", "yaml");
        map.insert("yml", "yaml");  // yml -> yaml for ripgrep
        map.insert("toml", "toml");
        
        map
    }
    
    /// Parse type parameter from Python (string or list) into official ripgrep type names
    fn parse_types(type_param: Option<&PyAny>) -> PyResult<Vec<String>> {
        let type_mapping = Self::create_type_mapping();
        let mut result_types = Vec::new();
        
        if let Some(param) = type_param {
            if let Ok(type_str) = param.extract::<&str>() {
                // Single string type
                if let Some(&official_name) = type_mapping.get(type_str) {
                    result_types.push(official_name.to_string());
                } else {
                    return Err(PyValueError::new_err(format!("Unknown file type: {}", type_str)));
                }
            } else if let Ok(type_list) = param.extract::<Vec<&str>>() {
                // List of types
                for type_str in type_list {
                    if let Some(&official_name) = type_mapping.get(type_str) {
                        result_types.push(official_name.to_string());
                    } else {
                        return Err(PyValueError::new_err(format!("Unknown file type: {}", type_str)));
                    }
                }
            } else {
                return Err(PyValueError::new_err("Type parameter must be a string or list of strings"));
            }
        }
        
        Ok(result_types)
    }

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

    /// Search for content with context (GIL-free inner implementation)
    fn search_content_inner(
        &self,
        matcher: &RegexMatcher,
        walker: ignore::Walk,
        type_matcher: Option<&ignore::types::Types>,
        before_context: u64,
        after_context: u64,
        deadline: Option<Instant>,
    ) -> Result<Vec<ContentResult>, RGErr> {
        let mut results = Vec::new();

        for entry in walker {
            if timed_out(deadline) {
                return Err(RGErr::Timeout);
            }

            let entry = entry.map_err(RGErr::Walk)?;

            if !entry.file_type().map_or(false, |ft| ft.is_file()) {
                continue;
            }

            // Apply type filter manually for AND logic with glob
            if let Some(type_matcher) = type_matcher {
                if !type_matcher.matched(entry.path(), false).is_whitelist() {
                    continue;
                }
            }

            self.search_file_content_inner(
                matcher,
                entry.path(),
                before_context,
                after_context,
                &mut results,
            )?;
        }

        Ok(results)
    }

    /// Search for files containing matches (GIL-free inner implementation)
    fn search_files_inner(
        &self,
        matcher: &RegexMatcher,
        walker: ignore::Walk,
        type_matcher: Option<&ignore::types::Types>,
        head_limit: Option<usize>,
        deadline: Option<Instant>,
    ) -> Result<Vec<String>, RGErr> {
        let mut files = HashSet::new();
        let mut searcher = Searcher::new(); // Create once, reuse for all files

        for entry in walker {
            if timed_out(deadline) {
                return Err(RGErr::Timeout);
            }

            if let Some(limit) = head_limit {
                if files.len() >= limit {
                    break;
                }
            }

            let entry = entry.map_err(RGErr::Walk)?;

            if !entry.file_type().map_or(false, |ft| ft.is_file()) {
                continue;
            }

            // Apply type filter manually for AND logic with glob
            if let Some(type_matcher) = type_matcher {
                if !type_matcher.matched(entry.path(), false).is_whitelist() {
                    continue;
                }
            }

            if self.file_has_match_inner_with_searcher(&mut searcher, matcher, entry.path())? {
                files.insert(entry.path().to_string_lossy().to_string());
            }
        }

        Ok(files.into_iter().collect())
    }

    /// Search and count matches per file (GIL-free inner implementation)
    fn search_count_inner(
        &self,
        matcher: &RegexMatcher,
        walker: ignore::Walk,
        type_matcher: Option<&ignore::types::Types>,
        head_limit: Option<usize>,
        deadline: Option<Instant>,
    ) -> Result<Vec<CountResult>, RGErr> {
        let mut counts = Vec::new();
        let mut searcher = Searcher::new(); // Create once, reuse for all files

        for entry in walker {
            if timed_out(deadline) {
                return Err(RGErr::Timeout);
            }

            if let Some(limit) = head_limit {
                if counts.len() >= limit {
                    break;
                }
            }

            let entry = entry.map_err(RGErr::Walk)?;

            if !entry.file_type().map_or(false, |ft| ft.is_file()) {
                continue;
            }

            // Apply type filter manually for AND logic with glob
            if let Some(type_matcher) = type_matcher {
                if !type_matcher.matched(entry.path(), false).is_whitelist() {
                    continue;
                }
            }

            let count = self.count_matches_in_file_inner_with_searcher(&mut searcher, matcher, entry.path())?;
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
        types: &[String],
    ) -> PyResult<(ignore::Walk, Option<ignore::types::Types>)> {
        let path_buf = PathBuf::from(path);
        if !path_buf.exists() {
            return Err(PyValueError::new_err(format!("Path not found: {}", path)));
        }

        let mut builder = WalkBuilder::new(&path_buf);
        builder
            .hidden(true)
            .git_ignore(true)
            .git_global(true)
            .git_exclude(true)
            .follow_links(false)
            .parents(true)
            .ignore(true)
            .standard_filters(true);

        // Build type matcher separately for manual checking (AND logic)
        let type_matcher = if !types.is_empty() {
            let mut tb = TypesBuilder::new();
            tb.add_defaults();
            for t in types {
                tb.select(t);
            }
            Some(tb.build()
                .map_err(|e| PyValueError::new_err(format!("Invalid file type configuration: {e}")))?)
        } else {
            None
        };

        // Use overrides for glob filtering (fast pruning during traversal)
        if let Some(pat) = glob {
            let mut ob = OverrideBuilder::new(&path_buf);
            ob.add("!**").map_err(|e| PyValueError::new_err(format!("Invalid glob: {e}")))?;
            ob.add(pat).map_err(|e| PyValueError::new_err(format!("Invalid glob: {e}")))?;
            let overrides = ob.build()
                .map_err(|e| PyValueError::new_err(format!("Failed to build glob overrides: {e}")))?;
            builder.overrides(overrides);
        }

        Ok((builder.build(), type_matcher))
    }




    /// Search a single file for content with context
    fn search_file_content_inner(
        &self,
        matcher: &RegexMatcher,
        path: &Path,
        before_context: u64,
        after_context: u64,
        results: &mut Vec<ContentResult>,
    ) -> Result<(), RGErr> {
        use std::io::{BufRead, BufReader};

        let file = File::open(path).map_err(RGErr::Io)?;

        let path_str = path.to_string_lossy().to_string();
        let reader = BufReader::new(file);
        let lines: Result<Vec<String>, _> = reader.lines().collect();

        let lines = match lines {
            Ok(lines) => lines,
            Err(_) => return Ok(()), // Skip problematic files silently
        };

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

    /// Check if file has any matches with reused searcher
    fn file_has_match_inner_with_searcher(&self, searcher: &mut Searcher, matcher: &RegexMatcher, path: &Path) -> Result<bool, RGErr> {
        let file = File::open(path).map_err(RGErr::Io)?;

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

    /// Check if file has any matches
    fn file_has_match_inner(&self, matcher: &RegexMatcher, path: &Path) -> Result<bool, RGErr> {
        let mut searcher = Searcher::new();
        self.file_has_match_inner_with_searcher(&mut searcher, matcher, path)
    }

    /// Count matches in a file with reused searcher
    fn count_matches_in_file_inner_with_searcher(&self, searcher: &mut Searcher, matcher: &RegexMatcher, path: &Path) -> Result<u64, RGErr> {
        let file = File::open(path).map_err(RGErr::Io)?;

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

    /// Count matches in a file
    fn count_matches_in_file_inner(&self, matcher: &RegexMatcher, path: &Path) -> Result<u64, RGErr> {
        let mut searcher = Searcher::new();
        self.count_matches_in_file_inner_with_searcher(&mut searcher, matcher, path)
    }

    /// Format content results for Python to match ripgrep CLI output
    fn format_content_results(
        &self,
        py: Python,
        results: Vec<ContentResult>,
        show_line_numbers: bool,
        head_limit: Option<usize>,
    ) -> PyResult<PyObject> {
        if results.is_empty() {
            return Ok(Vec::<String>::new().into_py(py));
        }

        use std::collections::{BTreeMap, HashMap};

        // Group results by file without cloning paths
        let mut file_groups: HashMap<&str, Vec<&ContentResult>> = HashMap::new();
        for r in &results {
            file_groups.entry(&r.path).or_default().push(r);
        }

        let mut py_results: Vec<String> = Vec::new();
        let mut first_file = true;

        for (file_path, mut file_results) in file_groups {
            // Add separator between different files (except first file)
            if !first_file && !py_results.is_empty() {
                if let Some(limit) = head_limit {
                    if py_results.len() >= limit {
                        break;
                    }
                }
                py_results.push("--".to_string());
            }
            first_file = false;

            // Sort results by line number
            file_results.sort_by_key(|r| r.line_number);

            // Build merged continuous ranges
            let mut merged_ranges: Vec<(u64, u64, Vec<(u64, String, bool)>)> = Vec::new();
            let mut current_start: u64 = 0;
            let mut current_end: u64 = 0;
            // line_num -> (content, is_match)
            let mut current_lines: BTreeMap<u64, (String, bool)> = BTreeMap::new();

            // helper to finalize a range
            let mut finalize_range = |start: u64,
                                      end: u64,
                                      lines: BTreeMap<u64, (String, bool)>,
                                      out: &mut Vec<(u64, u64, Vec<(u64, String, bool)>)>| {
                if end > 0 {
                    let vec_lines = lines
                        .into_iter()
                        .map(|(ln, (s, m))| (ln, s, m))
                        .collect::<Vec<_>>();
                    out.push((start, end, vec_lines));
                }
            };

            for result in file_results.iter() {
                let before_len = result.before_context.len() as u64;
                let after_len = result.after_context.len() as u64;

                // NOTE: keep exact arithmetic semantics (no saturating_sub) to preserve behavior.
                let range_start = result.line_number - before_len;
                let range_end = if after_len == 0 {
                    result.line_number
                } else {
                    result.line_number + after_len
                };

                // start new range if non-overlapping (> current_end + 1)
                if current_end == 0 || range_start > current_end + 1 {
                    // finalize previous
                    finalize_range(current_start, current_end, std::mem::take(&mut current_lines), &mut merged_ranges);

                    current_start = range_start;
                    current_end = range_end;
                } else {
                    // extend current
                    if range_end > current_end {
                        current_end = range_end;
                    }
                }

                // merge lines for this result into current_lines (prefer match over context)
                // before context
                for (i, before_line) in result.before_context.iter().enumerate() {
                    let ln = result.line_number - before_len + i as u64;
                    current_lines.entry(ln).or_insert_with(|| (before_line.clone(), false));
                }
                // the match line
                current_lines
                    .entry(result.line_number)
                    .and_modify(|e| {
                        if !e.1 {
                            *e = (result.content.clone(), true);
                        }
                    })
                    .or_insert_with(|| (result.content.clone(), true));
                // after context
                for (i, after_line) in result.after_context.iter().enumerate() {
                    let ln = result.line_number + 1 + i as u64;
                    current_lines.entry(ln).or_insert_with(|| (after_line.clone(), false));
                }
            }

            // finalize last range
            finalize_range(current_start, current_end, current_lines, &mut merged_ranges);

            // Output merged ranges
            for (i, (_start, _end, lines)) in merged_ranges.iter().enumerate() {
                if i > 0 {
                    if let Some(limit) = head_limit {
                        if py_results.len() >= limit {
                            break;
                        }
                    }
                    py_results.push("--".to_string());
                }

                for (line_num, content, is_match) in lines {
                    if let Some(limit) = head_limit {
                        if py_results.len() >= limit {
                            break;
                        }
                    }

                    let formatted = if show_line_numbers {
                        if *is_match {
                            format!("{file_path}:{line_num}:{content}")
                        } else {
                            format!("{file_path}-{line_num}:{content}")
                        }
                    } else {
                        format!("{file_path}:{content}")
                    };
                    py_results.push(formatted);
                }
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
