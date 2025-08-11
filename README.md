# ripgrep-python

A Python native binding for [ripgrep](https://github.com/BurntSushi/ripgrep), a fast recursive search tool written in Rust.

This library provides a true native integration with ripgrep's Rust API, not just a subprocess wrapper, offering excellent performance and seamless integration with Python.

## Features

- **Fast recursive search** using ripgrep's core engine
- **Native integration** (no subprocess overhead)
- **Rich search options** (case sensitivity, file type filtering, glob patterns, etc.)
- **Multiple output modes** (content with line numbers, file lists, match counts)
- **ripgrep-like interface** that closely mirrors the original ripgrep command-line experience
- **Full regex support** with multiline capabilities
- **Context support** (before/after lines)
- **Pythonic API** with full type hints and IDE support
- **Type-safe** with complete `.pyi` stub files for static analysis

## Installation

- Linux: x86_64, aarch64, i686, armv7, s390x, ppc64le
- Windows: x64, x86
- macOS: Intel (x86_64), Apple Silicon (aarch64)

### From PyPI
```sh
pip install ripgrep-python
```

### From Source

You'll need Rust and Cargo installed (see [Rust installation guide](https://www.rust-lang.org/tools/install)).

```sh
# Clone the repository
git clone https://github.com/LinXueyuanStdio/ripgrep-python.git
cd ripgrep-python

# Build and install the package
pip install maturin
maturin develop
```

## Quick Start

The interface provides a `Grep` class that closely mirrors ripgrep's command-line interface:

```python
import pyripgrep

# Create a grep instance
grep = pyripgrep.Grep()

# Basic search - find files containing 'pattern'
files = grep.search("pattern")
print(files)  # ['file1.py', 'file2.rs', ...]

# Search with content and line numbers
content = grep.search("pattern", output_mode="content", n=True)
print(content)  # ['file1.py:42:matching line', ...]

# Count matches per file
counts = grep.search("pattern", output_mode="count")
print(counts)  # {'file1.py': 5, 'file2.rs': 12, ...}

# Advanced filtering
results = grep.search(
    "struct",
    path="src/",
    type="rust",
    i=True,
    C=2,
    head_limit=10
)
```
## API Documentation

The main interface is the `Grep` class, which provides a unified search method with various options:

```python
from typing import Dict, List, Literal, Optional, Union

def search(
    self,
    pattern: str,                                           # Required: regex pattern to search for
    path: Optional[str] = None,                            # Path to search (default: current directory)
    glob: Optional[str] = None,                            # Glob pattern for file filtering (e.g., "*.py")
    output_mode: Optional[Literal["content", "files_with_matches", "count"]] = None,  # Output format
    B: Optional[int] = None,                               # Lines before match (-B flag)
    A: Optional[int] = None,                               # Lines after match (-A flag)
    C: Optional[int] = None,                               # Lines before and after match (-C flag)
    n: Optional[bool] = None,                              # Show line numbers (-n flag)
    i: Optional[bool] = None,                              # Case insensitive search (-i flag)
    type: Optional[str] = None,                            # File type filter (e.g., "rust", "python")
    head_limit: Optional[int] = None,                      # Limit number of results
    multiline: Optional[bool] = None                       # Enable multiline mode (-U flag)
) -> Union[List[str], Dict[str, int]]:
    """
    Search for pattern in files with various options.

    Returns:
        - List[str]: When output_mode is "files_with_matches" (default) or "content"
        - Dict[str, int]: When output_mode is "count" (filename -> match count)
    """
```

### Output Modes

#### `files_with_matches` (default)
Returns list of file paths containing matches:
```python
files = grep.search("TODO")
# Returns: ['src/main.rs', 'docs/readme.md', ...]
```

#### `content`
Returns matching lines with optional context and line numbers:
```python
# Basic content search
lines = grep.search("function", output_mode="content")
# Returns: ['src/app.js:function myFunc() {', ...]

# With line numbers and context
lines = grep.search("error", output_mode="content",
                   n=True, C=2)
```

#### `count`
Returns match counts per file:
```python
counts = grep.search("import", output_mode="count")
# Returns: {'src/main.py': 15, 'src/utils.py': 8, ...}
```

## Usage Examples

### Basic Search
```python
import pyripgrep

grep = pyripgrep.Grep()

# Find all files containing "TODO"
files = grep.search("TODO")
for file in files:
    print(file)

# Show actual matching lines
content = grep.search("TODO", output_mode="content", n=True)
for line in content[:5]:  # First 5 matches
    print(line)
```

### File Type Filtering
```python
# Search only in Rust files
rust_files = grep.search("struct", type="rust")

# Search only in Python files
py_files = grep.search("def", type="python")

# Supported: rust, python, javascript, typescript, java, c, cpp, go, etc.
```

### Advanced Filtering
```python
# Use glob patterns
js_files = grep.search("function", glob="*.js")

# Case insensitive search
files = grep.search("ERROR", i=True)

# Search in specific directory with context
results = grep.search(
    "impl",
    path="src/",
    output_mode="content",
    C=3,
    n=True,
    head_limit=10
)
```

### Regular Expressions
```python
# Find function definitions
functions = grep.search(r"fn\s+\w+", output_mode="content", type="rust")

# Find import statements
imports = grep.search(r"^(import|from)\s+", output_mode="content", type="python")

# Multiline matching
structs = grep.search(r"struct\s+\w+\s*\{", multiline=True, output_mode="content")
```

### Performance and Statistics
```python
import time

# Time a search operation
start = time.time()
results = grep.search("pattern", path="large_directory/")
duration = time.time() - start

print(f"Found {len(results)} files in {duration:.3f} seconds")

# Get detailed match counts
counts = grep.search("pattern", output_mode="count")
total_matches = sum(counts.values())
print(f"Total matches: {total_matches} across {len(counts)} files")
```

## Comparison with ripgrep CLI

| ripgrep command | Python equivalent |
|----------------|-------------------|
| `rg pattern` | `grep.search("pattern")` |
| `rg pattern -l` | `grep.search("pattern", output_mode="files_with_matches")` |
| `rg pattern -n` | `grep.search("pattern", output_mode="content", n=True)` |
| `rg pattern -c` | `grep.search("pattern", output_mode="count")` |
| `rg pattern -i` | `grep.search("pattern", i=True)` |
| `rg pattern -A 3` | `grep.search("pattern", A=3, output_mode="content")` |
| `rg pattern -B 3` | `grep.search("pattern", B=3, output_mode="content")` |
| `rg pattern -C 3` | `grep.search("pattern", C=3, output_mode="content")` |
| `rg pattern -t py` | `grep.search("pattern", type="python")` |
| `rg pattern -g "*.js"` | `grep.search("pattern", glob="*.js")` |
| `rg pattern -U` | `grep.search("pattern", multiline=True)` |

## Type Annotations

This library provides full type hint support for better IDE experience and static type checking:

### Type-Safe API

```python
from typing import Dict, List
import pyripgrep

# Create typed instance
grep: pyripgrep.Grep = pyripgrep.Grep()

# Type inference for different output modes
files: List[str] = grep.search("pattern")  # files_with_matches mode
content: List[str] = grep.search("pattern", output_mode="content")  # content mode
counts: Dict[str, int] = grep.search("pattern", output_mode="count")  # count mode
```

### IDE Support

The library includes complete `.pyi` stub files providing:

- **IntelliSense**: Full autocompletion in VS Code, PyCharm, etc.
- **Type checking**: Works with mypy, pyright, and other static analyzers
- **Method overloads**: Different return types based on `output_mode` parameter
- **Parameter hints**: Detailed documentation for all parameters

### Example with Type Annotations

```python
from typing import Dict, List
import pyripgrep

def analyze_codebase(pattern: str, directory: str) -> Dict[str, int]:
    """Analyze codebase for pattern occurrences with full type safety."""
    grep: pyripgrep.Grep = pyripgrep.Grep()

    # Type checker knows this returns Dict[str, int]
    counts: Dict[str, int] = grep.search(
        pattern,
        path=directory,
        output_mode="count",
        i=True
    )

    return counts

# Usage with type checking
results: Dict[str, int] = analyze_codebase("TODO", "src/")
total_todos: int = sum(results.values())
```

For more examples, see `examples/typed_usage_demo.py` and `docs/TYPE_ANNOTATIONS.md`.

## Development

### Building from Source

#### Prerequisites

1. **Install Rust toolchain**:
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source ~/.cargo/env
   ```

2. **Install Python development dependencies**:
   ```bash
   pip install maturin
   ```

#### Build and Install

```bash
# Clone the repository
git clone https://github.com/LinXueyuanStdio/ripgrep-python.git
cd ripgrep-python

# Development build (creates importable module)
maturin develop

# Or build wheel for distribution
maturin build --release
```

#### Running Examples

```bash
# Run the new interface demo
python examples/new_interface_demo.py

# Run basic usage example
python examples/basic_usage.py

# Run performance tests
python examples/test_new_interface.py
```

#### Testing

```bash
# Run Python tests
python -m pytest tests/ -v

# Test the module import
python -c "import pyripgrep; print('Import successful')"
```

### Publishing

For maintainers and contributors:

```sh
# Build for current platform
make build

# Build for all platforms
make build-all

# Publish to TestPyPI
make publish-test

# Publish to PyPI
make publish-prod
```

See [Publishing Guide](docs/PUBLISHING.md) for detailed cross-platform build instructions.

## Migration Guide

If you're using the old interface (`RipGrep` class), here's how to migrate to the new `Grep` class:

### Old Interface
```python
import pyripgrep

rg = pyripgrep.RipGrep()
options = pyripgrep.SearchOptions()
options.case_sensitive = False

results = rg.search("pattern", ["."], options)
files = rg.search_files("pattern", ["."], options)
counts = rg.count_matches("pattern", ["."], options)
```

### New Interface
```python
import pyripgrep

grep = pyripgrep.Grep()

# Search with content (equivalent to old search method)
results = grep.search("pattern", i=True, output_mode="content")

# Search for files (equivalent to old search_files method)
files = grep.search("pattern", i=True, output_mode="files_with_matches")

# Count matches (equivalent to old count_matches method)
counts = grep.search("pattern", i=True, output_mode="count")
```

## Performance

This library provides native Rust performance through direct API integration:

- **No subprocess overhead** - direct Rust function calls
- **Optimized file walking** - uses ripgrep's ignore crate for .gitignore support
- **Binary detection** - automatically skips binary files
- **Parallel processing** - leverages Rust's concurrency for large searches

Benchmark results show 10-50x performance improvement over subprocess-based solutions on large codebases.

## Troubleshooting

### Import Errors
If you get import errors, ensure maturin build completed successfully:
```bash
maturin develop --release
python -c "import pyripgrep; print('Success!')"
```

### Rust Toolchain Issues
Update Rust if you encounter build issues:
```bash
rustup update
```

### Performance Issues
For very large searches, consider using `head_limit` to restrict results:
```bash
# Limit to first 1000 results
results = grep.search("pattern", head_limit=1000)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run `maturin develop` to test locally
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [BurntSushi](https://github.com/BurntSushi) for the original ripgrep tool
- [PyO3](https://github.com/PyO3/pyo3) for Rust-Python bindings
- [Maturin](https://github.com/PyO3/maturin) for building and packaging
