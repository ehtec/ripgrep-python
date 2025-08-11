#!/usr/bin/env python3
"""
Test suite for the Grep interface that matches the specified tool schema.

This test validates the exact interface as defined in the schema:
- Required parameter: pattern
- Optional parameters: path, glob, output_mode, -B, -A, -C, -n, -i, type, head_limit, multiline
- Output modes: content, files_with_matches (default), count
"""

import pytest
import pyripgrep
import os
import tempfile
import json
from typing import List, Dict, Union


class TestGrepInterface:
    """Test class for the new Grep interface"""

    def setup_method(self):
        """Setup test environment with sample files"""
        # Create temporary directory
        self.tmpdir = tempfile.mkdtemp()

        # Create test files with various content
        self.test_files = {
            "main.py": """#!/usr/bin/env python3
import os
import sys
from typing import Dict

def main():
    print("Hello World")
    return 0

class Logger:
    def __init__(self):
        self.logs = []

    def error(self, msg):
        print(f"ERROR: {msg}")
""",
            "app.js": """// JavaScript application
function greet(name) {
    console.log(`Hello ${name}!`);
}

const logger = {
    error: function(msg) {
        console.error('ERROR:', msg);
    }
};

greet('World');
""",
            "lib.rs": """// Rust library
use std::collections::HashMap;

pub struct Config {
    pub settings: HashMap<String, String>,
}

impl Config {
    pub fn new() -> Self {
        Config {
            settings: HashMap::new(),
        }
    }

    pub fn error(&self, msg: &str) {
        eprintln!("ERROR: {}", msg);
    }
}
""",
            "README.md": """# Test Project

This is a test project for **ripgrep-python**.

## Features
- Fast search
- Multiple output modes
- Regular expression support

## Usage
Run `grep.search()` to search files.

ERROR handling is important.
"""
        }

        # Write test files
        for filename, content in self.test_files.items():
            filepath = os.path.join(self.tmpdir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

        # Create subdirectory with more files
        self.subdir = os.path.join(self.tmpdir, "src")
        os.makedirs(self.subdir)

        with open(os.path.join(self.subdir, "utils.py"), 'w') as f:
            f.write("""def helper():
    return "utility function"

def error_handler():
    raise Exception("Test error")
""")

    def teardown_method(self):
        """Cleanup test files"""
        import shutil
        if os.path.exists(self.tmpdir):
            shutil.rmtree(self.tmpdir)

    def test_grep_instantiation(self):
        """Test that Grep class can be instantiated"""
        grep = pyripgrep.Grep()
        assert grep is not None

    def test_basic_search_required_pattern_only(self):
        """Test basic search with only required pattern parameter"""
        grep = pyripgrep.Grep()

        # Search in current directory - should find files with "ERROR"
        results = grep.search("ERROR", path=self.tmpdir)
        assert isinstance(results, list)
        assert len(results) > 0

        # All results should be file paths
        for result in results:
            assert isinstance(result, str)
            assert os.path.isfile(result)

    def test_output_modes(self):
        """Test all three output modes"""
        grep = pyripgrep.Grep()

        # Test files_with_matches mode (default)
        files = grep.search("ERROR", path=self.tmpdir, output_mode="files_with_matches")
        assert isinstance(files, list)
        assert all(isinstance(f, str) for f in files)
        assert len(files) > 0

        # Test content mode
        content = grep.search("ERROR", path=self.tmpdir, output_mode="content")
        assert isinstance(content, list)
        assert all(isinstance(line, str) for line in content)
        assert len(content) > 0

        # Content should contain file paths and content
        for line in content:
            assert ":" in line  # Should have path:content format

        # Test count mode
        counts = grep.search("ERROR", path=self.tmpdir, output_mode="count")
        assert isinstance(counts, dict)
        assert len(counts) > 0

        # Counts should map file paths to integers
        for filepath, count in counts.items():
            assert isinstance(filepath, str)
            assert isinstance(count, int)
            assert count > 0

    def test_context_parameters(self):
        """Test -A, -B, and -C context parameters"""
        grep = pyripgrep.Grep()

        # Test -A (after context) - requires output_mode="content"
        results_a = grep.search("ERROR", path=self.tmpdir, output_mode="content", A=2)
        assert isinstance(results_a, list)
        assert len(results_a) > 0

        # Test -B (before context) - requires output_mode="content"
        results_b = grep.search("ERROR", path=self.tmpdir, output_mode="content", B=2)
        assert isinstance(results_b, list)
        assert len(results_b) > 0

        # Test -C (context both ways) - requires output_mode="content"
        results_c = grep.search("ERROR", path=self.tmpdir, output_mode="content", C=2)
        assert isinstance(results_c, list)
        assert len(results_c) > 0

    def test_line_numbers_flag(self):
        """Test -n flag for showing line numbers"""
        grep = pyripgrep.Grep()

        # Line numbers only work with content mode
        results_with_nums = grep.search("ERROR", path=self.tmpdir, output_mode="content", n=True)
        results_without_nums = grep.search("ERROR", path=self.tmpdir, output_mode="content", n=False)

        assert isinstance(results_with_nums, list)
        assert isinstance(results_without_nums, list)

        # With line numbers, format should be path:line_num:content
        for result in results_with_nums:
            parts = result.split(":", 2)  # Split only on first 2 colons
            assert len(parts) >= 2

        # Without line numbers, format should be path:content
        for result in results_without_nums:
            assert isinstance(result, str)

    def test_case_insensitive_flag(self):
        """Test -i flag for case insensitive search"""
        grep = pyripgrep.Grep()

        # Search for lowercase "error" with case sensitivity
        sensitive_results = grep.search("error", path=self.tmpdir, i=False)

        # Search for lowercase "error" without case sensitivity
        insensitive_results = grep.search("error", path=self.tmpdir, i=True)

        # Case insensitive should find more results (includes "ERROR")
        assert len(insensitive_results) >= len(sensitive_results)

    def test_file_type_filter(self):
        """Test type parameter for file type filtering"""
        grep = pyripgrep.Grep()

        # Search only in Python files
        py_results = grep.search("import", path=self.tmpdir, type="python")
        assert isinstance(py_results, list)

        # All results should be Python files
        for filepath in py_results:
            assert filepath.endswith('.py')

        # Search only in Rust files
        rust_results = grep.search("struct", path=self.tmpdir, type="rust")
        assert isinstance(rust_results, list)

        # All results should be Rust files
        for filepath in rust_results:
            assert filepath.endswith('.rs')

        # Search only in JavaScript files
        js_results = grep.search("function", path=self.tmpdir, type="js")
        assert isinstance(js_results, list)

        # All results should be JS files
        for filepath in js_results:
            assert filepath.endswith('.js')

    def test_glob_filter(self):
        """Test glob parameter for file filtering"""
        grep = pyripgrep.Grep()

        # Search only Python files using glob
        py_glob_results = grep.search("def", path=self.tmpdir, glob="*.py")
        assert isinstance(py_glob_results, list)

        # All results should be Python files
        for filepath in py_glob_results:
            assert filepath.endswith('.py')

        # Search only Rust files using glob
        rust_glob_results = grep.search("use", path=self.tmpdir, glob="*.rs")
        assert isinstance(rust_glob_results, list)

        # All results should be Rust files
        for filepath in rust_glob_results:
            assert filepath.endswith('.rs')

    def test_head_limit_parameter(self):
        """Test head_limit parameter to limit results"""
        grep = pyripgrep.Grep()

        # Get all results first
        all_results = grep.search("e", path=self.tmpdir, output_mode="content")

        # Limit to 3 results
        limited_results = grep.search("e", path=self.tmpdir, output_mode="content", head_limit=3)

        assert len(limited_results) <= 3
        assert len(limited_results) <= len(all_results)

        # Test with files_with_matches mode
        all_files = grep.search("e", path=self.tmpdir, output_mode="files_with_matches")
        limited_files = grep.search("e", path=self.tmpdir, output_mode="files_with_matches", head_limit=2)

        assert len(limited_files) <= 2
        assert len(limited_files) <= len(all_files)

        # Test with count mode
        all_counts = grep.search("e", path=self.tmpdir, output_mode="count")
        limited_counts = grep.search("e", path=self.tmpdir, output_mode="count", head_limit=2)

        assert len(limited_counts) <= 2
        assert len(limited_counts) <= len(all_counts)

    def test_multiline_parameter(self):
        """Test multiline parameter for cross-line pattern matching"""
        grep = pyripgrep.Grep()

        # Create a test file with multiline content
        multiline_file = os.path.join(self.tmpdir, "multiline.txt")
        with open(multiline_file, 'w') as f:
            f.write("""struct Config {
    pub name: String,
    pub value: i32,
}""")

        # Search for pattern that spans multiple lines
        # Note: This is a simplified test - real multiline regex can be complex
        results = grep.search(r"struct.*\{", path=self.tmpdir, multiline=True, output_mode="content")
        assert isinstance(results, list)

    def test_path_parameter(self):
        """Test path parameter for specifying search location"""
        grep = pyripgrep.Grep()

        # Search in specific subdirectory
        subdir_results = grep.search("helper", path=self.subdir)
        assert isinstance(subdir_results, list)
        assert len(subdir_results) > 0

        # All results should be in subdirectory
        for filepath in subdir_results:
            assert self.subdir in filepath

    def test_regex_patterns(self):
        """Test various regex patterns"""
        grep = pyripgrep.Grep()

        # Test literal string
        literal_results = grep.search("ERROR", path=self.tmpdir)
        assert len(literal_results) > 0

        # Test regex with word boundaries
        word_results = grep.search(r"\bERROR\b", path=self.tmpdir, output_mode="content")
        assert len(word_results) > 0

        # Test regex with character classes
        func_results = grep.search(r"function\s+\w+", path=self.tmpdir, output_mode="content")
        assert isinstance(func_results, list)

    def test_error_handling(self):
        """Test error handling for invalid parameters"""
        grep = pyripgrep.Grep()

        # Test invalid output mode
        with pytest.raises(Exception):
            grep.search("test", path=self.tmpdir, output_mode="invalid_mode")

        # Test invalid path
        with pytest.raises(Exception):
            grep.search("test", path="/nonexistent/path/that/does/not/exist")

    def test_empty_results(self):
        """Test behavior when no matches are found"""
        grep = pyripgrep.Grep()

        # Search for pattern that should not exist
        no_results = grep.search("XYZPATTERNNOTFOUNDXYZ", path=self.tmpdir)
        assert isinstance(no_results, list)
        assert len(no_results) == 0

        # Test with content mode
        no_content = grep.search("XYZPATTERNNOTFOUNDXYZ", path=self.tmpdir, output_mode="content")
        assert isinstance(no_content, list)
        assert len(no_content) == 0

        # Test with count mode
        no_counts = grep.search("XYZPATTERNNOTFOUNDXYZ", path=self.tmpdir, output_mode="count")
        assert isinstance(no_counts, dict)
        assert len(no_counts) == 0

    def test_performance_with_large_search(self):
        """Test performance characteristics with larger search"""
        grep = pyripgrep.Grep()

        # Search for common character with head limit
        import time
        start_time = time.time()

        results = grep.search("e", path=self.tmpdir, head_limit=100)

        end_time = time.time()
        search_time = end_time - start_time

        # Should complete reasonably quickly (within 5 seconds)
        assert search_time < 5.0
        assert isinstance(results, list)

    def test_combined_parameters(self):
        """Test using multiple parameters together"""
        grep = pyripgrep.Grep()

        # Combine multiple flags
        results = grep.search(
            "ERROR",
            path=self.tmpdir,
            output_mode="content",
            i=True,           # case insensitive
            n=True,           # line numbers
            C=1,              # context lines
            type="python",    # Python files only
            head_limit=5      # limit results
        )

        assert isinstance(results, list)
        assert len(results) <= 5

        # Results should be from Python files only
        for result in results:
            # Format should be path:line_num:content due to -n flag
            assert isinstance(result, str)
            assert result.count(":") >= 2  # At least path:line_num:content

    def test_default_behavior(self):
        """Test default behavior matches specification"""
        grep = pyripgrep.Grep()

        # Default output mode should be files_with_matches
        default_results = grep.search("ERROR", path=self.tmpdir)
        explicit_results = grep.search("ERROR", path=self.tmpdir, output_mode="files_with_matches")

        assert sorted(default_results) == sorted(explicit_results), f"Default {default_results} != Explicit {explicit_results}"

        # Verify they are both lists
        assert isinstance(default_results, list), f"Expected list, got {type(default_results)}"
        assert isinstance(explicit_results, list), f"Expected list, got {type(explicit_results)}"

        # Default path should be current working directory (but we specify for testing)
        # Default case sensitivity should be case-sensitive
        # Default multiline should be False
        # Default line numbers should be False


def run_comprehensive_test():
    """Run a comprehensive test of the Grep interface"""
    print("Running comprehensive Grep interface tests...")

    # Create test instance
    test_instance = TestGrepInterface()

    try:
        # Run all tests
        test_methods = [method for method in dir(test_instance) if method.startswith('test_')]

        passed = 0
        failed = 0

        for method_name in test_methods:
            try:
                print(f"  Running {method_name}...")
                test_instance.setup_method()
                method = getattr(test_instance, method_name)
                method()
                test_instance.teardown_method()
                passed += 1
                print(f"    ✓ PASSED")
            except Exception as e:
                failed += 1
                print(f"    ✗ FAILED: {e}")
                test_instance.teardown_method()

        print(f"\nTest Results: {passed} passed, {failed} failed")
        return failed == 0

    except Exception as e:
        print(f"Test setup failed: {e}")
        return False


if __name__ == "__main__":
    # Run tests directly
    success = run_comprehensive_test()
    if success:
        print("\n🎉 All tests passed! The Grep interface is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the implementation.")
        exit(1)
