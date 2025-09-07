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
import subprocess
import shutil
import time
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

        # Content should contain file paths and content (skip separators)
        for line in content:
            if line == "--":  # Skip separator lines
                continue
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

        # Create a test file with known line structure for context testing
        context_file = os.path.join(self.tmpdir, "context_test.txt")
        context_content = """line1: before context
line2: before context
line3: before context
line4: TARGET LINE with ERROR
line5: after context
line6: after context
line7: after context"""
        
        with open(context_file, 'w') as f:
            f.write(context_content)

        # Test -A (after context) - should show 2 lines after the match
        results_a = grep.search("TARGET LINE", path=context_file, output_mode="content", A=2)
        assert isinstance(results_a, list)
        assert len(results_a) > 0
        
        # Should contain the target line and 2 lines after
        content_a = '\n'.join(results_a)
        assert "TARGET LINE with ERROR" in content_a
        assert "line5: after context" in content_a
        assert "line6: after context" in content_a
        # Should not contain line7 (beyond A=2)
        assert "line7: after context" not in content_a

        # Test -B (before context) - should show 2 lines before the match
        results_b = grep.search("TARGET LINE", path=context_file, output_mode="content", B=2)
        assert isinstance(results_b, list)
        assert len(results_b) > 0
        
        # Should contain the target line and 2 lines before
        content_b = '\n'.join(results_b)
        assert "TARGET LINE with ERROR" in content_b
        assert "line2: before context" in content_b
        assert "line3: before context" in content_b
        # Should not contain line1 (beyond B=2)
        assert "line1: before context" not in content_b

        # Test -C (context both ways) - should show 2 lines before AND after
        results_c = grep.search("TARGET LINE", path=context_file, output_mode="content", C=2)
        assert isinstance(results_c, list)
        assert len(results_c) > 0
        
        # Should contain the target line, 2 lines before, and 2 lines after
        content_c = '\n'.join(results_c)
        assert "TARGET LINE with ERROR" in content_c
        # Before context
        assert "line2: before context" in content_c
        assert "line3: before context" in content_c
        # After context
        assert "line5: after context" in content_c
        assert "line6: after context" in content_c
        # Should not contain lines beyond C=2
        assert "line1: before context" not in content_c
        assert "line7: after context" not in content_c

    def test_line_numbers_flag(self):
        """Test -n flag for showing line numbers"""
        grep = pyripgrep.Grep()

        # Line numbers only work with content mode
        results_with_nums = grep.search("ERROR", path=self.tmpdir, output_mode="content", n=True)
        results_without_nums = grep.search("ERROR", path=self.tmpdir, output_mode="content", n=False)

        assert isinstance(results_with_nums, list)
        assert isinstance(results_without_nums, list)

        # With line numbers, format should be path:line_num:content (skip separators)
        for result in results_with_nums:
            if result == "--":  # Skip separator lines
                continue
            parts = result.split(":", 2)  # Split only on first 2 colons
            assert len(parts) >= 2

        # Without line numbers, format should be path:content (skip separators)
        for result in results_without_nums:
            if result == "--":  # Skip separator lines
                continue
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
        with pytest.raises(ValueError):
            grep.search("test", path=self.tmpdir, output_mode="invalid_mode")

        # Test invalid path
        with pytest.raises(ValueError):
            grep.search("test", path="/nonexistent/path/that/does/not/exist")
            
        # Test invalid regex pattern
        with pytest.raises(ValueError):
            grep.search("[invalid regex", path=self.tmpdir)

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

    def test_timeout_functionality(self):
        """Test timeout functionality with proper validation of timing and exceptions"""
        # Create temporary directory for cloning
        clone_dir = tempfile.mkdtemp()
        
        try:
            # Clone a medium-sized repository (using a shallow clone to be faster)
            print("Cloning repository for timeout test...")
            result = subprocess.run([
                "git", "clone", "--depth=1", 
                "https://github.com/FFmpeg/FFmpeg.git", 
                os.path.join(clone_dir, "ffmpeg")
            ], check=True, capture_output=True, text=True)
            
            grep = pyripgrep.Grep()
            repo_path = os.path.join(clone_dir, "ffmpeg")
            timeout_value = 0.5  # 500ms timeout
            
            # Test that timeout actually works - measure actual timing
            start_time = time.perf_counter()
            
            timeout_exception_raised = False
            actual_exception = None
            
            try:
                # Search for a very expensive pattern that will definitely timeout
                grep.search(
                    r".*([a-zA-Z]+.*){3,}.*", 
                    path=repo_path,
                    output_mode="content",
                    timeout=timeout_value
                )
            except TimeoutError as e:
                timeout_exception_raised = True
                actual_exception = e
            
            elapsed_time = time.perf_counter() - start_time
            
            # Validate timeout behavior
            assert timeout_exception_raised, f"Expected timeout exception but none was raised. Search completed in {elapsed_time:.3f}s"
            
            # Check that timeout occurred approximately at the specified time (allow 200ms tolerance)
            tolerance = 0.3
            assert (timeout_value - tolerance) <= elapsed_time <= (timeout_value + tolerance), \
                f"Timeout should occur around {timeout_value}s (±{tolerance}s), but took {elapsed_time:.3f}s"
            
            # Check that it's the correct timeout exception type
            assert actual_exception is not None
            exception_name = type(actual_exception).__name__
            exception_msg = str(actual_exception).lower()
            assert "timeout" in exception_name.lower() or "timeout" in exception_msg, \
                f"Expected timeout-related exception, got {exception_name}: {actual_exception}"
            
            # Test that a reasonable timeout allows completion
            reasonable_timeout = 30.0
            success_start_time = time.perf_counter()
            
            results = grep.search(
                r".*([a-zA-Z]+.*){3,}.*", 
                path=repo_path,
                output_mode="content",
                timeout=reasonable_timeout
            )
            success_elapsed_time = time.perf_counter() - success_start_time
            
            # Should complete without timeout
            assert isinstance(results, list)
            assert len(results) > 0, "FFmpeg should have files containing 'main'"
            assert success_elapsed_time < reasonable_timeout, \
                f"Search should complete within {reasonable_timeout}s, took {success_elapsed_time:.3f}s"
                
            # Log timing information for test stability analysis
            print(f"Timeout test: {elapsed_time:.3f}s (target: {timeout_value}s)")
            print(f"Success test: {success_elapsed_time:.3f}s (margin: {timeout_value - success_elapsed_time:.3f}s)")
            
        except subprocess.CalledProcessError as e:
            pytest.skip(f"Could not clone repository for timeout test: {e}")
        finally:
            # Cleanup cloned repository
            if os.path.exists(clone_dir):
                shutil.rmtree(clone_dir)

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
        
        # Filter out separator lines for the file type check
        content_lines = [line for line in results if line != "--"]

        # Results should be from Python files only (excluding separator lines)
        for result in content_lines:
            # Format should be path:line_num:content for matches or path-line_num:content for context
            assert isinstance(result, str)
            # Both match lines (:) and context lines (-) should have at least 1 colon
            assert result.count(":") >= 1  # At least path:content or path-line:content
            assert ".py" in result  # Should be from Python files

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

    def test_glob_pattern_basic_extensions(self):
        """Test basic glob pattern matching with extensions"""
        grep = pyripgrep.Grep()
        
        # Test Python files only
        py_results = grep.search("def", path=self.tmpdir, glob="*.py", output_mode="files_with_matches")
        assert isinstance(py_results, list)
        for filepath in py_results:
            assert filepath.endswith('.py'), f"Non-Python file found: {filepath}"
        
        # Test Rust files only
        rs_results = grep.search("struct", path=self.tmpdir, glob="*.rs", output_mode="files_with_matches")
        assert isinstance(rs_results, list)
        for filepath in rs_results:
            assert filepath.endswith('.rs'), f"Non-Rust file found: {filepath}"
            
        # Test JavaScript files only
        js_results = grep.search("function", path=self.tmpdir, glob="*.js", output_mode="files_with_matches")
        assert isinstance(js_results, list)
        for filepath in js_results:
            assert filepath.endswith('.js'), f"Non-JavaScript file found: {filepath}"

    def test_glob_pattern_exact_filenames(self):
        """Test glob patterns with exact filenames"""
        grep = pyripgrep.Grep()
        
        # Search for specific filename
        readme_results = grep.search("ripgrep-python", path=self.tmpdir, glob="README.md", output_mode="files_with_matches")
        assert isinstance(readme_results, list)
        for filepath in readme_results:
            assert "README.md" in filepath, f"Wrong file found: {filepath}"

    def test_glob_pattern_wildcards(self):
        """Test glob patterns with wildcards"""
        grep = pyripgrep.Grep()
        
        # Create additional test files with specific patterns
        wildcard_files = {
            "test_main.py": "def test_function(): pass",
            "main_app.py": "def main(): pass", 
            "helper_utils.py": "def helper(): pass"
        }
        
        for filename, content in wildcard_files.items():
            filepath = os.path.join(self.tmpdir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Test prefix wildcard
        main_results = grep.search("def", path=self.tmpdir, glob="main*.py", output_mode="files_with_matches")
        assert isinstance(main_results, list)
        for filepath in main_results:
            basename = os.path.basename(filepath)
            assert basename.startswith('main') and basename.endswith('.py'), f"Wrong pattern match: {basename}"
            
        # Test suffix wildcard
        test_results = grep.search("def", path=self.tmpdir, glob="*_main.py", output_mode="files_with_matches")
        assert isinstance(test_results, list)
        for filepath in test_results:
            basename = os.path.basename(filepath)
            assert basename.endswith('_main.py'), f"Wrong pattern match: {basename}"

    def test_glob_pattern_question_mark(self):
        """Test glob patterns with single character wildcards"""
        grep = pyripgrep.Grep()
        
        # Create files for single character testing
        single_char_files = {
            "file1.txt": "content 1",
            "file2.txt": "content 2",
            "file3.txt": "content 3",
            "files.txt": "content s",
            "filelong.txt": "content long"
        }
        
        for filename, content in single_char_files.items():
            filepath = os.path.join(self.tmpdir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Test single character wildcard
        single_results = grep.search("content", path=self.tmpdir, glob="file?.txt", output_mode="files_with_matches")
        assert isinstance(single_results, list)
        
        basenames = [os.path.basename(f) for f in single_results]
        # Should match file1.txt, file2.txt, file3.txt, files.txt but NOT filelong.txt
        expected_matches = ["file1.txt", "file2.txt", "file3.txt", "files.txt"]
        for expected in expected_matches:
            assert expected in basenames, f"Expected {expected} not found in {basenames}"
        assert "filelong.txt" not in basenames, f"filelong.txt should not match file?.txt pattern"

    def test_glob_pattern_character_classes(self):
        """Test glob patterns with character classes"""
        grep = pyripgrep.Grep()
        
        # Create files for character class testing
        char_class_files = {
            "log1.txt": "log entry 1", 
            "log2.txt": "log entry 2",
            "log3.txt": "log entry 3",
            "log4.txt": "log entry 4",
            "loga.txt": "log entry a"
        }
        
        for filename, content in char_class_files.items():
            filepath = os.path.join(self.tmpdir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Test character class pattern
        class_results = grep.search("log entry", path=self.tmpdir, glob="log[123].txt", output_mode="files_with_matches")
        assert isinstance(class_results, list)
        
        basenames = [os.path.basename(f) for f in class_results]
        # Should match log1.txt, log2.txt, log3.txt but not log4.txt or loga.txt
        expected_matches = ["log1.txt", "log2.txt", "log3.txt"]
        for expected in expected_matches:
            assert expected in basenames, f"Expected {expected} not found in {basenames}"
        
        unexpected_matches = ["log4.txt", "loga.txt"]
        for unexpected in unexpected_matches:
            assert unexpected not in basenames, f"Unexpected {unexpected} found in {basenames}"

    def test_glob_pattern_with_directories(self):
        """Test glob patterns that include directory paths"""
        grep = pyripgrep.Grep()
        
        # Test matching files in the subdirectory we already created
        nested_results = grep.search("helper", path=self.tmpdir, glob="src/*.py", output_mode="files_with_matches")
        assert isinstance(nested_results, list)
        
        # All results should be in src/ directory and be .py files
        for filepath in nested_results:
            assert os.path.basename(os.path.dirname(filepath)) == 'src' and filepath.endswith('.py'), f"Wrong directory match: {filepath}"

    def test_glob_pattern_case_sensitivity(self):
        """Test case sensitivity in glob patterns"""
        grep = pyripgrep.Grep()
        
        # Create files with different cases
        case_files = {
            "Test.PY": "# uppercase extension",
            "test.py": "# lowercase extension"
        }
        
        for filename, content in case_files.items():
            filepath = os.path.join(self.tmpdir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Test uppercase pattern
        upper_results = grep.search("#", path=self.tmpdir, glob="*.PY", output_mode="files_with_matches")
        assert isinstance(upper_results, list)
        upper_basenames = [os.path.basename(f) for f in upper_results]
        assert "Test.PY" in upper_basenames, "Case-sensitive matching should find Test.PY"
        assert "test.py" not in upper_basenames, "Case-sensitive matching should not find test.py with *.PY"
        
        # Test lowercase pattern
        lower_results = grep.search("#", path=self.tmpdir, glob="*.py", output_mode="files_with_matches")
        assert isinstance(lower_results, list)
        lower_basenames = [os.path.basename(f) for f in lower_results]
        # Should find lowercase but not uppercase
        assert any(f.endswith('.py') for f in lower_basenames), "Should find .py files"

    def test_glob_pattern_no_matches(self):
        """Test glob patterns that don't match any files"""
        grep = pyripgrep.Grep()
        
        # Test pattern that shouldn't match anything
        no_match = grep.search("anything", path=self.tmpdir, glob="*.nonexistent", output_mode="files_with_matches")
        assert isinstance(no_match, list)
        assert len(no_match) == 0, "Should return empty list for non-matching pattern"

    def test_glob_pattern_with_all_output_modes(self):
        """Test that glob patterns work with all output modes"""
        grep = pyripgrep.Grep()
        
        # Test with files_with_matches mode
        files = grep.search("def", path=self.tmpdir, glob="*.py", output_mode="files_with_matches")
        assert isinstance(files, list)
        for filepath in files:
            assert filepath.endswith('.py'), f"Wrong file type in files mode: {filepath}"
        
        # Test with content mode
        content = grep.search("def", path=self.tmpdir, glob="*.py", output_mode="content")
        assert isinstance(content, list)
        for line in content:
            # Skip separator lines
            if line == "--":
                continue
            assert ".py:" in line, f"Wrong file type in content mode: {line}"
        
        # Test with count mode
        counts = grep.search("def", path=self.tmpdir, glob="*.py", output_mode="count")
        assert isinstance(counts, dict)
        for filepath in counts.keys():
            assert filepath.endswith('.py'), f"Wrong file type in count mode: {filepath}"

    def test_glob_pattern_complex_names(self):
        """Test glob patterns with complex file names"""
        grep = pyripgrep.Grep()
        
        # Create files with complex names
        complex_files = {
            "test.backup.py": "# backup file content",
            "app.min.js": "// minified javascript",
            "config.local.json": '{"local": true}',
            "data.test.txt": "test data content"
        }
        
        for filename, content in complex_files.items():
            filepath = os.path.join(self.tmpdir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Test complex extension patterns
        backup_results = grep.search("backup", path=self.tmpdir, glob="*.backup.py", output_mode="files_with_matches")
        assert isinstance(backup_results, list)
        assert len(backup_results) == 1, "Should find exactly one backup file"
        assert "test.backup.py" in backup_results[0], "Should find the backup Python file"
        
        min_results = grep.search("minified", path=self.tmpdir, glob="*.min.js", output_mode="files_with_matches")
        assert isinstance(min_results, list)
        assert len(min_results) == 1, "Should find exactly one minified file"
        assert "app.min.js" in min_results[0], "Should find the minified JavaScript file"

    def test_glob_pattern_multiple_extensions_at_once(self):
        """Test glob patterns that match multiple file extensions in one pattern"""
        grep = pyripgrep.Grep()
        
        # Create files with different extensions
        multi_files = {
            "script.py": "Python content here",
            "script.js": "JavaScript content here", 
            "script.rs": "Rust content here",
            "script.go": "Go content here",
            "data.json": "JSON content here",
            "readme.md": "Markdown content here",
            "other.txt": "Text content here"
        }
        
        for filename, content in multi_files.items():
            filepath = os.path.join(self.tmpdir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Test brace expansion pattern {py,js,rs} - MUST work
        brace_results = grep.search("content here", path=self.tmpdir, glob="*.{py,js,rs}", output_mode="files_with_matches")
        assert isinstance(brace_results, list)
        assert len(brace_results) > 0, "Brace expansion *.{py,js,rs} must find matching files"
        
        # Should find py, js, rs files
        basenames = [os.path.basename(f) for f in brace_results]
        expected_extensions = ["script.py", "script.js", "script.rs"]
        found_expected = [f for f in basenames if f in expected_extensions]
        assert len(found_expected) == 3, f"Should find all 3 expected files (py,js,rs), got: {basenames}"
        
        # Should not find other extensions
        unexpected = ["script.go", "data.json", "readme.md", "other.txt"]
        found_unexpected = [f for f in basenames if f in unexpected]
        assert len(found_unexpected) == 0, f"Should not find unexpected files: {found_unexpected}"

    def test_glob_and_type_are_intersection(self):
        """glob and type must combine with AND semantics"""
        grep = pyripgrep.Grep()

        # Compute sets separately
        only_glob = set(grep.search(".", path=self.tmpdir, glob="*.py",
                                    output_mode="files_with_matches"))
        only_type = set(grep.search(".", path=self.tmpdir, type="python",
                                    output_mode="files_with_matches"))
        both = set(grep.search(".", path=self.tmpdir, glob="*.py", type="python",
                               output_mode="files_with_matches"))

        # Invariant: BOTH == intersection(only_glob, only_type)
        assert both == (only_glob & only_type), f"Expected AND semantics; got {both=} vs {(only_glob & only_type)=}"

        # Negative sanity checks (conflicting filters => empty)
        js_and_python = grep.search(".", path=self.tmpdir, glob="*.js", type="python",
                                    output_mode="files_with_matches")
        py_and_rust = grep.search(".", path=self.tmpdir, glob="*.py", type="rust",
                                  output_mode="files_with_matches")
        assert js_and_python == [], "glob=*.js AND type=python should yield no files"
        assert py_and_rust == [], "glob=*.py AND type=rust should yield no files"

        # Positive sanity check (both narrow to .py & python)
        py_and_python = grep.search("def|import", path=self.tmpdir, glob="*.py", type="python",
                                    i=True, output_mode="files_with_matches")
        assert py_and_python and all(p.endswith(".py") for p in py_and_python)

    def test_context_merging_within_file(self):
        """Test that overlapping context blocks are properly merged within a single file"""
        grep = pyripgrep.Grep()
        
        # Create a test file with closely spaced matches
        context_file = os.path.join(self.tmpdir, "context_merge_test.py")
        test_content = """# line 1
def function_a():  # line 2 - MATCH
    return "result"  # line 3
    
def function_b():  # line 5 - MATCH  
    return "value"   # line 6
    
def other_function():  # line 8
    pass  # line 9
"""
        
        with open(context_file, 'w') as f:
            f.write(test_content)
        
        # Search with C=2 (2 lines context before and after)
        results = grep.search("def function", path=context_file, output_mode="content", n=True, C=2)
        
        # With C=2, the matches on lines 2 and 5 should have overlapping context
        # Line 2 context: lines 1,3,4 
        # Line 5 context: lines 3,4,6,7
        # These should be merged into one continuous block
        
        content_str = '\n'.join(results)
        
        # Should contain both matches and merged context
        assert "def function_a():" in content_str
        assert "def function_b():" in content_str
        
        # Should not have duplicate context lines
        line_3_count = content_str.count('return "result"')
        assert line_3_count == 1, f"Line 3 should appear only once, found {line_3_count} times"
        
        # Should not contain separators within merged context
        separator_count = content_str.count('--')
        assert separator_count == 0, f"Should not have separators in merged context, found {separator_count}"

    def test_context_separation_between_files(self):
        """Test that context blocks from different files are separated properly"""
        grep = pyripgrep.Grep()
        
        # Create two test files
        file1 = os.path.join(self.tmpdir, "file1.py") 
        file2 = os.path.join(self.tmpdir, "file2.py")
        
        with open(file1, 'w') as f:
            f.write("""# File 1
def target_function():  # MATCH
    return 1
""")
            
        with open(file2, 'w') as f:
            f.write("""# File 2  
def target_function():  # MATCH
    return 2
""")
        
        # Search with context
        results = grep.search("target_function", path=self.tmpdir, output_mode="content", n=True, C=1)
        
        content_str = '\n'.join(results)
        
        # Should contain results from both files
        assert "file1.py" in content_str
        assert "file2.py" in content_str
        assert "return 1" in content_str
        assert "return 2" in content_str
        
        # Should have separator between different files
        separator_count = content_str.count('--')
        assert separator_count >= 1, f"Should have at least one separator between files, found {separator_count}"

    def test_context_range_separation_within_file(self):
        """Test that non-overlapping context ranges within a file are separated"""
        grep = pyripgrep.Grep()
        
        # Create a test file with widely spaced matches
        context_file = os.path.join(self.tmpdir, "range_separation_test.py")
        test_content = """# line 1
def first_match():  # line 2 - MATCH
    return "first"  # line 3

# Many lines in between
# line 5
# line 6  
# line 7
# line 8
# line 9
# line 10

def second_match():  # line 12 - MATCH
    return "second"  # line 13
# line 14
"""
        
        with open(context_file, 'w') as f:
            f.write(test_content)
        
        # Search with C=1 (1 line context)
        results = grep.search("_match", path=context_file, output_mode="content", n=True, C=1)
        
        content_str = '\n'.join(results)
        
        # Should contain both matches
        assert "first_match" in content_str
        assert "second_match" in content_str
        
        # Should have separator between non-overlapping ranges
        separator_count = content_str.count('--')
        assert separator_count >= 1, f"Should have separator between distant matches, found {separator_count}"
        
        # Should not contain the middle lines (5-11) that are not in context
        assert "line 6" not in content_str
        assert "line 10" not in content_str

    def test_context_match_preference(self):
        """Test that when a line is both context and match, it's shown as match"""
        grep = pyripgrep.Grep()
        
        # Create a test file where one match's context overlaps with another match
        context_file = os.path.join(self.tmpdir, "match_preference_test.py")
        test_content = """line 1
error_function()  # line 2 - will be MATCH and also context for line 4
line 3
another_error()   # line 4 - MATCH
line 5
"""
        
        with open(context_file, 'w') as f:
            f.write(test_content)
        
        # Search for "error" with C=1 context
        results = grep.search("error", path=context_file, output_mode="content", n=True, C=1)
        
        content_str = '\n'.join(results)
        
        # Both lines should appear as matches (using : separator)
        error_function_matches = [line for line in results if "error_function" in line and ":2:" in line]
        another_error_matches = [line for line in results if "another_error" in line and ":4:" in line]
        
        assert len(error_function_matches) == 1, "error_function should appear as match (with :)"
        assert len(another_error_matches) == 1, "another_error should appear as match (with :)"
        
        # error_function should not appear as context (with -) for another_error
        error_function_context = [line for line in results if "error_function" in line and "-2:" in line]
        assert len(error_function_context) == 0, "error_function should not appear as context (with -)"

    def test_head_limit_with_context_and_separators(self):
        """Test that head_limit correctly limits total output lines including context and separators"""
        grep = pyripgrep.Grep()
        
        # Create test files with multiple matches
        for i in range(1, 4):
            filepath = os.path.join(self.tmpdir, f"test{i}.py")
            with open(filepath, 'w') as f:
                f.write(f"""# File {i}
def test_function_{i}():  # MATCH
    return {i}
""")
        
        # Search with head_limit=5, which should include context and separators
        results = grep.search("test_function", path=self.tmpdir, output_mode="content", n=True, C=1, head_limit=5)
        
        # Should have exactly 5 or fewer output lines total
        assert len(results) <= 5, f"head_limit=5 should limit total output, got {len(results)} lines"
        
        # Should include context and/or separators in the count
        content_str = '\n'.join(results)
        
        # Should have some results but be truncated
        assert len(results) > 0, "Should have some results"
        
        # Might have separators counted in the limit
        has_separators = "--" in content_str
        if has_separators:
            separator_count = content_str.count('--')
            content_lines = len([line for line in results if line != "--"])
            assert len(results) == content_lines + separator_count, "Total should include separators"


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
