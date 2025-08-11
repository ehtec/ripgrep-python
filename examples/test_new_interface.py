#!/usr/bin/env python3
"""
Test the new Grep interface that matches the ripgrep-like functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import pyripgrep
    print(f"Successfully imported pyripgrep v{pyripgrep.__version__}")
except ImportError as e:
    print(f"Failed to import pyripgrep: {e}")
    sys.exit(1)

def test_basic_search():
    """Test basic search functionality"""
    print("\n=== Test 1: Basic search (files_with_matches mode) ===")

    grep = pyripgrep.Grep()

    # Search for 'use' in current directory
    result = grep.search(pattern="use", path=".", output_mode="files_with_matches")
    print(f"Files containing 'use': {result}")

def test_content_mode():
    """Test content mode with line numbers"""
    print("\n=== Test 2: Content mode with line numbers ===")

    grep = pyripgrep.Grep()

    # Search for 'fn' with content output and line numbers
    result = grep.search(
        pattern="fn",
        path="src",
        output_mode="content",
        line_numbers=True
    )
    print(f"Content results (first 5): {result[:5] if isinstance(result, list) else result}")

def test_case_insensitive():
    """Test case insensitive search"""
    print("\n=== Test 3: Case insensitive search ===")

    grep = pyripgrep.Grep()

    # Search for 'PYTHON' case insensitively
    result = grep.search(
        pattern="PYTHON",
        path=".",
        output_mode="files_with_matches",
        case_insensitive=True
    )
    print(f"Files containing 'PYTHON' (case insensitive): {result}")

def test_file_type_filter():
    """Test file type filtering"""
    print("\n=== Test 4: File type filtering ===")

    grep = pyripgrep.Grep()

    # Search only in Rust files
    try:
        result = grep.search(
            pattern="struct",
            path=".",
            output_mode="files_with_matches",
            file_type="rust"
        )
        print(f"Rust files containing 'struct': {result}")
    except Exception as e:
        print(f"File type filtering error (expected): {e}")

def test_count_mode():
    """Test count mode"""
    print("\n=== Test 5: Count mode ===")

    grep = pyripgrep.Grep()

    # Count matches
    result = grep.search(
        pattern="fn",
        path="src",
        output_mode="count"
    )
    print(f"Match counts: {result}")

def test_glob_pattern():
    """Test glob pattern filtering"""
    print("\n=== Test 6: Glob pattern filtering ===")

    grep = pyripgrep.Grep()

    # Search in .rs files only
    try:
        result = grep.search(
            pattern="pub",
            path=".",
            output_mode="files_with_matches",
            glob="*.rs"
        )
        print(f"Files matching '*.rs' containing 'pub': {result}")
    except Exception as e:
        print(f"Glob filtering error: {e}")

def test_context():
    """Test context lines"""
    print("\n=== Test 7: Context lines ===")

    grep = pyripgrep.Grep()

    # Search with context
    result = grep.search(
        pattern="impl",
        path="src",
        output_mode="content",
        context=2,
        line_numbers=True
    )
    print(f"Results with context (first 3): {result[:3] if isinstance(result, list) else result}")

def test_head_limit():
    """Test head limit"""
    print("\n=== Test 8: Head limit ===")

    grep = pyripgrep.Grep()

    # Limit results
    result = grep.search(
        pattern="use",
        path=".",
        output_mode="files_with_matches",
        head_limit=3
    )
    print(f"Limited results: {result}")

def main():
    """Run all tests"""
    print("Testing new Grep interface...")

    try:
        test_basic_search()
        test_content_mode()
        test_case_insensitive()
        test_file_type_filter()
        test_count_mode()
        test_glob_pattern()
        test_context()
        test_head_limit()

        print("\n=== All tests completed ===")

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
