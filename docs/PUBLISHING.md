# Cross-Platform Publishing Guide

This guide explains how to build and publish `ripgrep-python` across multiple platforms using the provided tools.

## Quick Start

### 1. Basic Publishing

```bash
# Build and test locally
./scripts/publish.sh build-only

# Publish to TestPyPI
./scripts/publish.sh test

# Publish to PyPI (production)
./scripts/publish.sh prod
```

### 2. Cross-Platform Building

```bash
# Setup cross-compilation tools
./scripts/cross-compile.sh setup

# Build for all supported platforms
./scripts/cross-compile.sh build-all

# Build for specific platform
./scripts/cross-compile.sh build x86_64-unknown-linux-gnu
```

### 3. Docker-based Building

```bash
# Setup Docker buildx
./scripts/docker-build.sh setup

# Build for multiple platforms using Docker
./scripts/docker-build.sh build --platforms linux/amd64,linux/arm64
```

## Supported Platforms

### Linux
- x86_64 (Intel/AMD 64-bit)
- aarch64 (ARM 64-bit)
- i686 (Intel/AMD 32-bit)
- armv7 (ARM 32-bit)
- s390x (IBM Z)
- ppc64le (PowerPC 64-bit LE)

### Windows
- x64 (Intel/AMD 64-bit)
- x86 (Intel/AMD 32-bit)

### macOS
- x86_64 (Intel Macs)
- aarch64 (Apple Silicon M1/M2/M3)

## GitHub Actions Automation

The project includes automated CI/CD that:

1. **Builds** wheels for all supported platforms
2. **Tests** installation and basic functionality
3. **Publishes** to PyPI when tags are created

### Triggering Builds

```bash
# Create and push a version tag
git tag v0.1.1
git push origin v0.1.1

# Manual trigger via GitHub Actions UI
# Go to Actions → Build and Publish → Run workflow
```

### Environment Setup

Add these secrets to your GitHub repository:

- `PYPI_API_TOKEN` - Your PyPI API token
- `TEST_PYPI_API_TOKEN` - Your TestPyPI API token

## Local Development

### Prerequisites

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Python build tools
pip install maturin twine

# Install cross-compilation tools (optional)
cargo install cross
```

### Building Locally

```bash
# Simple local build
maturin build --release

# Build with specific target
maturin build --release --target x86_64-apple-darwin

# Build and install for development
maturin develop
```

## Publishing Process

### 1. Prepare Release

```bash
# Update version in pyproject.toml
# Update CHANGELOG.md
# Commit changes
git add .
git commit -m "Prepare release v0.1.1"
```

### 2. Test Release

```bash
# Test build locally
./scripts/publish.sh build-only --clean

# Test publish to TestPyPI
export TEST_PYPI_TOKEN="your-test-token"
./scripts/publish.sh test
```

### 3. Production Release

```bash
# Create version tag
git tag v0.1.1
git push origin v0.1.1

# Or manual publish
export PYPI_TOKEN="your-prod-token"
./scripts/publish.sh prod
```

## Troubleshooting

### Common Issues

**Build fails on specific platform:**
- Check if Rust target is installed: `rustup target list`
- Install missing target: `rustup target add TARGET_NAME`

**Cross-compilation fails:**
- Install cross: `cargo install cross`
- Use Docker-based build instead

**Publishing fails:**
- Verify API token is set correctly
- Check if version already exists on PyPI
- Use `--skip-existing` flag

### Platform-Specific Notes

**Linux:**
- Uses manylinux wheels for maximum compatibility
- Requires Docker for some cross-compilation targets

**Windows:**
- Requires Visual Studio Build Tools
- Use Windows runner in CI for best results

**macOS:**
- Can build both Intel and Apple Silicon from M1/M2 Macs
- May require Xcode command line tools

## Monitoring and Maintenance

### Health Checks

```bash
# Test installation from PyPI
pip install ripgrep-python
python -c "import pyripgrep; print('OK')"

# Check package metadata
pip show ripgrep-python

# Verify all platforms
# Check download stats at https://pypistats.org/packages/ripgrep-python
```

### Update Process

1. Update dependencies in `Cargo.toml`
2. Update Python metadata in `pyproject.toml`
3. Test locally across platforms
4. Update documentation
5. Create release tag
6. Monitor CI/CD pipeline
7. Verify publication on PyPI

## Resources

- [PyPI Package](https://pypi.org/project/ripgrep-python/)
- [TestPyPI Package](https://test.pypi.org/project/ripgrep-python/)
- [GitHub Repository](https://github.com/LinXueyuanStdio/ripgrep-python)
- [Maturin Documentation](https://maturin.rs/)
- [PyO3 Documentation](https://pyo3.rs/)
