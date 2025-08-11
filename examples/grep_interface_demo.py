#!/usr/bin/env python3
"""
Demo script for the new Grep interface that matches the tool specification.

This script demonstrates all the features of the Grep class with the exact
parameter names and behavior as specified in the schema.
"""

import pyripgrep
import os
import tempfile


def create_demo_files():
    """Create demo files for testing"""
    # Create temporary directory
    tmpdir = tempfile.mkdtemp()
    print(f"Created demo directory: {tmpdir}")

    # Demo files with different content
    files = {
        "main.py": '''#!/usr/bin/env python3
"""Main application module"""
import os
import sys
from typing import Dict, List

def main():
    """Entry point function"""
    print("Hello World")
    logger = Logger()
    logger.error("Test error message")
    return 0

class Logger:
    def __init__(self):
        self.logs: List[str] = []

    def error(self, message: str):
        """Log error message"""
        print(f"ERROR: {message}")
        self.logs.append(f"ERROR: {message}")

if __name__ == "__main__":
    main()
''',

        "utils.js": '''// JavaScript utility functions
function greet(name) {
    console.log(`Hello ${name}!`);
}

const logger = {
    error: function(message) {
        console.error('ERROR:', message);
    },

    info: function(message) {
        console.log('INFO:', message);
    }
};

// Function with error handling
function processData(data) {
    try {
        return data.map(item => item.value);
    } catch (error) {
        logger.error(`Failed to process data: ${error.message}`);
        return [];
    }
}

greet('World');
''',

        "lib.rs": '''//! Rust library module
use std::collections::HashMap;
use std::error::Error;

/// Configuration structure
pub struct Config {
    pub name: String,
    pub settings: HashMap<String, String>,
}

impl Config {
    /// Create new config instance
    pub fn new(name: String) -> Self {
        Config {
            name,
            settings: HashMap::new(),
        }
    }

    /// Log error message
    pub fn error(&self, msg: &str) -> Result<(), Box<dyn Error>> {
        eprintln!("ERROR [{}]: {}", self.name, msg);
        Ok(())
    }

    /// Process function with error handling
    pub fn process(&self, data: Vec<String>) -> Result<Vec<String>, Box<dyn Error>> {
        let results: Vec<String> = data
            .into_iter()
            .map(|item| format!("processed: {}", item))
            .collect();
        Ok(results)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_creation() {
        let config = Config::new("test".to_string());
        assert_eq!(config.name, "test");
    }
}
''',

        "README.md": '''# Demo Project

This is a **demo project** for testing ripgrep-python functionality.

## Features
- Multiple programming languages
- Error handling examples
- Various search patterns

## Files
- `main.py` - Python main module
- `utils.js` - JavaScript utilities
- `lib.rs` - Rust library
- `README.md` - This file

## Search Examples
You can search for:
- `ERROR` - Error messages across all files
- `function` - Function definitions
- `struct` - Rust struct definitions
- `import` - Python imports

ERROR: This line contains an error message for testing.
'''
    }

    # Write demo files
    for filename, content in files.items():
        filepath = os.path.join(tmpdir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    # Create subdirectory
    subdir = os.path.join(tmpdir, "src")
    os.makedirs(subdir)

    with open(os.path.join(subdir, "helper.py"), 'w') as f:
        f.write('''def helper_function():
    """Helper utility function"""
    return "utility result"

def error_handler(message):
    """Handle error messages"""
    print(f"HANDLING ERROR: {message}")
''')

    return tmpdir


def demo_basic_usage(tmpdir):
    """Demo basic usage with required pattern parameter"""
    print("\n" + "="*60)
    print("1. BASIC USAGE - Required pattern parameter only")
    print("="*60)

    grep = pyripgrep.Grep()

    # Basic search with just pattern (uses default output mode)
    print("Searching for 'ERROR' in demo files...")
    results = grep.search("ERROR", path=tmpdir)

    print(f"Found {len(results)} files containing 'ERROR':")
    for filepath in results:
        filename = os.path.basename(filepath)
        print(f"  - {filename}")


def demo_output_modes(tmpdir):
    """Demo all three output modes"""
    print("\n" + "="*60)
    print("2. OUTPUT MODES - files_with_matches, content, count")
    print("="*60)

    grep = pyripgrep.Grep()

    # files_with_matches mode (default)
    print("\n2.1 files_with_matches mode (default):")
    files = grep.search("function", path=tmpdir, output_mode="files_with_matches")
    print(f"Files containing 'function': {len(files)}")
    for filepath in files:
        print(f"  - {os.path.basename(filepath)}")

    # content mode
    print("\n2.2 content mode:")
    content = grep.search("function", path=tmpdir, output_mode="content")
    print(f"Content matches for 'function': {len(content)}")
    for line in content[:5]:  # Show first 5 matches
        print(f"  {line}")

    # count mode
    print("\n2.3 count mode:")
    counts = grep.search("error", path=tmpdir, output_mode="count", i=True)  # case insensitive
    print("Match counts per file:")
    for filepath, count in counts.items():
        filename = os.path.basename(filepath)
        print(f"  {filename}: {count} matches")


def demo_context_flags(tmpdir):
    """Demo -A, -B, -C context flags"""
    print("\n" + "="*60)
    print("3. CONTEXT FLAGS - -A, -B, -C (require output_mode='content')")
    print("="*60)

    grep = pyripgrep.Grep()

    # -A flag: lines after match
    print("\n3.1 -A flag (2 lines after each match):")
    results_a = grep.search("ERROR", path=tmpdir, output_mode="content", A=2)
    for line in results_a[:3]:  # Show first 3 matches
        print(f"  {line}")

    # -B flag: lines before match
    print("\n3.2 -B flag (2 lines before each match):")
    results_b = grep.search("ERROR", path=tmpdir, output_mode="content", B=2)
    for line in results_b[:3]:
        print(f"  {line}")

    # -C flag: lines before and after match
    print("\n3.3 -C flag (2 lines before and after each match):")
    results_c = grep.search("ERROR", path=tmpdir, output_mode="content", C=2)
    for line in results_c[:3]:
        print(f"  {line}")


def demo_flags(tmpdir):
    """Demo -n and -i flags"""
    print("\n" + "="*60)
    print("4. FLAGS - -n (line numbers), -i (case insensitive)")
    print("="*60)

    grep = pyripgrep.Grep()

    # -n flag: show line numbers (requires output_mode="content")
    print("\n4.1 -n flag (show line numbers):")
    results_with_nums = grep.search("import", path=tmpdir, output_mode="content", n=True)
    for line in results_with_nums[:3]:
        print(f"  {line}")

    print("\n4.2 Without line numbers:")
    results_no_nums = grep.search("import", path=tmpdir, output_mode="content", n=False)
    for line in results_no_nums[:3]:
        print(f"  {line}")

    # -i flag: case insensitive
    print("\n4.3 Case sensitive search for 'error':")
    sensitive = grep.search("error", path=tmpdir, i=False)
    print(f"  Found {len(sensitive)} files")

    print("\n4.4 Case insensitive search for 'error' (-i flag):")
    insensitive = grep.search("error", path=tmpdir, i=True)
    print(f"  Found {len(insensitive)} files (includes 'ERROR')")


def demo_file_filtering(tmpdir):
    """Demo file type and glob filtering"""
    print("\n" + "="*60)
    print("5. FILE FILTERING - type and glob parameters")
    print("="*60)

    grep = pyripgrep.Grep()

    # type parameter
    print("\n5.1 type='python' (filter by file type):")
    py_files = grep.search("def", path=tmpdir, type="python")
    for filepath in py_files:
        print(f"  - {os.path.basename(filepath)}")

    print("\n5.2 type='javascript':")
    js_files = grep.search("function", path=tmpdir, type="javascript")
    for filepath in js_files:
        print(f"  - {os.path.basename(filepath)}")

    print("\n5.3 type='rust':")
    rust_files = grep.search("struct", path=tmpdir, type="rust")
    for filepath in rust_files:
        print(f"  - {os.path.basename(filepath)}")

    # glob parameter
    print("\n5.4 glob='*.py' (filter by glob pattern):")
    glob_py = grep.search("import", path=tmpdir, glob="*.py")
    for filepath in glob_py:
        print(f"  - {os.path.basename(filepath)}")

    print("\n5.5 glob='*.rs':")
    glob_rust = grep.search("use", path=tmpdir, glob="*.rs")
    for filepath in glob_rust:
        print(f"  - {os.path.basename(filepath)}")


def demo_head_limit(tmpdir):
    """Demo head_limit parameter"""
    print("\n" + "="*60)
    print("6. HEAD LIMIT - Limit number of results")
    print("="*60)

    grep = pyripgrep.Grep()

    # head_limit with different output modes
    print("\n6.1 All results for 'e' (common character):")
    all_results = grep.search("e", path=tmpdir, output_mode="content")
    print(f"  Total matches: {len(all_results)}")

    print("\n6.2 Limited to 5 results (head_limit=5):")
    limited = grep.search("e", path=tmpdir, output_mode="content", head_limit=5)
    print(f"  Limited matches: {len(limited)}")
    for line in limited:
        print(f"    {line}")

    print("\n6.3 head_limit with count mode:")
    all_counts = grep.search("e", path=tmpdir, output_mode="count")
    limited_counts = grep.search("e", path=tmpdir, output_mode="count", head_limit=3)
    print(f"  All count entries: {len(all_counts)}")
    print(f"  Limited count entries: {len(limited_counts)}")


def demo_regex_patterns(tmpdir):
    """Demo regular expression patterns"""
    print("\n" + "="*60)
    print("7. REGEX PATTERNS - Regular expressions and multiline")
    print("="*60)

    grep = pyripgrep.Grep()

    # Word boundaries
    print("\n7.1 Word boundaries - \\bERROR\\b:")
    word_boundary = grep.search(r"\bERROR\b", path=tmpdir, output_mode="content")
    for line in word_boundary:
        print(f"  {line}")

    # Function patterns
    print("\n7.2 Function definitions - function\\s+\\w+:")
    func_pattern = grep.search(r"function\s+\w+", path=tmpdir, output_mode="content")
    for line in func_pattern:
        print(f"  {line}")

    # Multiline mode (simplified test)
    print("\n7.3 Multiline mode (multiline=True):")
    multiline_results = grep.search("struct.*Config", path=tmpdir, multiline=True, output_mode="content")
    for line in multiline_results:
        print(f"  {line}")


def demo_combined_parameters(tmpdir):
    """Demo combining multiple parameters"""
    print("\n" + "="*60)
    print("8. COMBINED PARAMETERS - Multiple flags together")
    print("="*60)

    grep = pyripgrep.Grep()

    print("\n8.1 Complex search - ERROR in Python files with context and line numbers:")
    complex_results = grep.search(
        "ERROR",                    # pattern
        path=tmpdir,                # search path
        output_mode="content",      # show content
        type="python",              # Python files only
        i=True,                     # case insensitive
        n=True,                     # show line numbers
        C=1,                        # 1 line context before/after
        head_limit=5                # limit to 5 results
    )

    print(f"Found {len(complex_results)} results:")
    for line in complex_results:
        print(f"  {line}")

    print("\n8.2 JavaScript functions with case insensitive search:")
    js_functions = grep.search(
        "function",
        path=tmpdir,
        output_mode="content",
        glob="*.js",
        i=True,
        n=True
    )

    for line in js_functions:
        print(f"  {line}")


def demo_path_parameter(tmpdir):
    """Demo path parameter for different search locations"""
    print("\n" + "="*60)
    print("9. PATH PARAMETER - Search in specific locations")
    print("="*60)

    grep = pyripgrep.Grep()

    # Search in main directory
    print(f"\n9.1 Search in main directory ({tmpdir}):")
    main_results = grep.search("function", path=tmpdir)
    print(f"  Found {len(main_results)} files")

    # Search in subdirectory
    subdir = os.path.join(tmpdir, "src")
    print(f"\n9.2 Search in subdirectory ({subdir}):")
    sub_results = grep.search("function", path=subdir)
    print(f"  Found {len(sub_results)} files")
    for filepath in sub_results:
        print(f"    - {os.path.basename(filepath)}")


def run_comprehensive_demo():
    """Run comprehensive demo of all Grep features"""
    print("🔍 COMPREHENSIVE DEMO: ripgrep-python Grep Interface")
    print("="*80)
    print("This demo shows all features matching the tool specification:")
    print("- Required: pattern")
    print("- Optional: path, glob, output_mode, -B, -A, -C, -n, -i, type, head_limit, multiline")

    # Create demo files
    tmpdir = create_demo_files()

    try:
        # Run all demos
        demo_basic_usage(tmpdir)
        demo_output_modes(tmpdir)
        demo_context_flags(tmpdir)
        demo_flags(tmpdir)
        demo_file_filtering(tmpdir)
        demo_head_limit(tmpdir)
        demo_regex_patterns(tmpdir)
        demo_combined_parameters(tmpdir)
        demo_path_parameter(tmpdir)

        print("\n" + "="*80)
        print("🎉 DEMO COMPLETE - All Grep interface features demonstrated!")
        print(f"📁 Demo files created in: {tmpdir}")
        print("💡 The interface matches the exact specification with parameters:")
        print("   pattern (required), path, glob, output_mode, -B, -A, -C, -n, -i, type, head_limit, multiline")
        print("="*80)

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up demo directory: {tmpdir}")
        import shutil
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)


if __name__ == "__main__":
    run_comprehensive_demo()
