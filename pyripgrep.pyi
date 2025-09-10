"""
Type stubs for pyripgrep module.

This module provides a Python binding for ripgrep, a fast recursive search tool.
"""

from typing import Dict, List, Literal, Optional, Union, overload

class Grep:
    """
    Main Grep interface that provides ripgrep-like functionality.

    This class mirrors the ripgrep command-line interface, providing methods
    to search through files and directories with various filtering options.
    """

    def __init__(self) -> None:
        """Initialize a new Grep instance."""
        ...

    # Overloaded signatures for different output modes
    @overload
    def search(
        self,
        pattern: Optional[str] = None,
        *,
        path: Optional[str] = None,
        glob: Optional[str] = None,
        output_mode: Literal["files_with_matches"] = "files_with_matches",
        B: Optional[int] = None,
        A: Optional[int] = None,
        C: Optional[int] = None,
        n: Optional[bool] = None,
        i: Optional[bool] = None,
        type: Optional[Union[str, List[str]]] = None,
        head_limit: Optional[int] = None,
        truncation_warning: Optional[bool] = None,
        multiline: Optional[bool] = None,
        timeout: Optional[float] = None,
    ) -> List[str]:
        """
        Search for pattern and return list of files containing matches.

        Args:
            pattern: Regular expression pattern to search for (required for this mode)
            path: Directory or file path to search (default: current directory)
            glob: Glob pattern for file filtering (e.g., "*.py")
            output_mode: Output mode - "files_with_matches" returns file paths
            B: Number of lines before each match to include (requires content mode)
            A: Number of lines after each match to include (requires content mode)
            C: Number of lines before and after each match (overrides A and B)
            n: Show line numbers (requires content mode)
            i: Case insensitive search
            type: File type filter (e.g., "rust", "python", ["python", "javascript"])
            head_limit: Maximum number of results to return
            truncation_warning: Add "[Content truncated]" message if results exceed head_limit
            multiline: Enable multiline mode
            timeout: Timeout in seconds for the search operation

        Returns:
            List of file paths containing matches
        """
        ...

    @overload
    def search(
        self,
        pattern: Optional[str] = None,
        *,
        path: Optional[str] = None,
        glob: Optional[str] = None,
        output_mode: Literal["content"],
        B: Optional[int] = None,
        A: Optional[int] = None,
        C: Optional[int] = None,
        n: Optional[bool] = None,
        i: Optional[bool] = None,
        type: Optional[Union[str, List[str]]] = None,
        head_limit: Optional[int] = None,
        truncation_warning: Optional[bool] = None,
        multiline: Optional[bool] = None,
        timeout: Optional[float] = None,
    ) -> List[str]:
        """
        Search for pattern and return matching lines with context.

        Args:
            pattern: Regular expression pattern to search for (required for this mode)
            path: Directory or file path to search (default: current directory)
            glob: Glob pattern for file filtering (e.g., "*.py")
            output_mode: Output mode - "content" returns matching lines
            B: Number of lines before each match to include
            A: Number of lines after each match to include
            C: Number of lines before and after each match (overrides A and B)
            n: Show line numbers in format "path:line_num:content"
            i: Case insensitive search
            type: File type filter (e.g., "rust", "python", ["python", "javascript"])
            head_limit: Maximum number of results to return
            truncation_warning: Add "[Content truncated]" message if results exceed head_limit
            multiline: Enable multiline mode
            timeout: Timeout in seconds for the search operation

        Returns:
            List of matching lines, optionally with line numbers and context.
            Format: "path:content" or "path:line_num:content" if n=True
        """
        ...

    @overload
    def search(
        self,
        pattern: Optional[str] = None,
        *,
        path: Optional[str] = None,
        glob: Optional[str] = None,
        output_mode: Literal["count"],
        B: Optional[int] = None,
        A: Optional[int] = None,
        C: Optional[int] = None,
        n: Optional[bool] = None,
        i: Optional[bool] = None,
        type: Optional[Union[str, List[str]]] = None,
        head_limit: Optional[int] = None,
        truncation_warning: Optional[bool] = None,
        multiline: Optional[bool] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, int]:
        """
        Search for pattern and return match counts per file.

        Args:
            pattern: Regular expression pattern to search for (required for this mode)
            path: Directory or file path to search (default: current directory)
            glob: Glob pattern for file filtering (e.g., "*.py")
            output_mode: Output mode - "count" returns match counts
            B: Number of lines before each match (ignored in count mode)
            A: Number of lines after each match (ignored in count mode)
            C: Number of lines before and after each match (ignored in count mode)
            n: Show line numbers (ignored in count mode)
            i: Case insensitive search
            type: File type filter (e.g., "rust", "python", ["python", "javascript"])
            head_limit: Maximum number of results to return
            truncation_warning: Add "[Content truncated]" message if results exceed head_limit
            multiline: Enable multiline mode
            timeout: Timeout in seconds for the search operation

        Returns:
            Dictionary mapping file paths to number of matches in each file
        """
        ...

    @overload
    def search(
        self,
        pattern: Optional[str] = None,
        *,
        path: Optional[str] = None,
        glob: Optional[str] = None,
        output_mode: Literal["files"],
        B: Optional[int] = None,
        A: Optional[int] = None,
        C: Optional[int] = None,
        n: Optional[bool] = None,
        i: Optional[bool] = None,
        type: Optional[Union[str, List[str]]] = None,
        head_limit: Optional[int] = None,
        truncation_warning: Optional[bool] = None,
        multiline: Optional[bool] = None,
        timeout: Optional[float] = None,
    ) -> List[str]:
        """
        List all files that would be searched (like rg --files).

        Args:
            pattern: Pattern is ignored in files mode (optional)
            path: Directory or file path to search (default: current directory)
            glob: Glob pattern for file filtering (e.g., "*.py")
            output_mode: Output mode - "files" returns all searchable file paths
            B: Number of lines before each match (ignored in files mode)
            A: Number of lines after each match (ignored in files mode)
            C: Number of lines before and after each match (ignored in files mode)
            n: Show line numbers (ignored in files mode)
            i: Case insensitive search (ignored in files mode)
            type: File type filter (e.g., "rust", "python", ["python", "javascript"])
            head_limit: Maximum number of results to return
            truncation_warning: Add "[Content truncated]" message if results exceed head_limit
            multiline: Enable multiline mode (ignored in files mode)
            timeout: Timeout in seconds for the search operation

        Returns:
            List of file paths that match the glob and type filters
        """
        ...
