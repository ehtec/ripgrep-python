#!/bin/bash

# publish.sh - Multi-platform build and publish script for ripgrep-python
# Usage: ./scripts/publish.sh [test|prod|build-only] [--platform TARGET] [--clean]

set -e  # Exit on error

# Configuration
PROJECT_NAME="ripgrep-python"
DIST_DIR="dist"
BUILD_DIR="target"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

show_help() {
    cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

Commands:
    build-only    Build wheels for all platforms but don't publish
    test          Build and publish to TestPyPI
    prod          Build and publish to PyPI
    help          Show this help message

Options:
    --platform TARGET    Build for specific platform (linux|windows|macos|all)
    --clean              Clean build artifacts before building
    --dry-run            Show what would be done without executing
    --skip-test          Skip installation testing

Platforms:
    linux     x86_64, aarch64, i686, armv7, s390x, ppc64le
    windows   x64, x86
    macos     x86_64 (Intel), aarch64 (Apple Silicon)
    all       All supported platforms (default)

Examples:
    $0 build-only --platform linux --clean
    $0 test --platform macos
    $0 prod

Environment Variables:
    PYPI_TOKEN         Token for PyPI (production)
    TEST_PYPI_TOKEN    Token for TestPyPI
    SKIP_BUILD         Skip building if wheels already exist
EOF
}

# Parse arguments
COMMAND=${1:-help}
PLATFORM="all"
CLEAN=false
DRY_RUN=false
SKIP_TEST=false

shift || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-test)
            SKIP_TEST=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate command
case $COMMAND in
    build-only|test|prod|help)
        ;;
    *)
        log_error "Invalid command: $COMMAND"
        show_help
        exit 1
        ;;
esac

if [[ $COMMAND == "help" ]]; then
    show_help
    exit 0
fi

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."

    if ! command -v maturin &> /dev/null; then
        log_error "maturin is not installed. Install with: pip install maturin"
        exit 1
    fi

    if ! command -v python &> /dev/null; then
        log_error "Python is not installed"
        exit 1
    fi

    log_success "Dependencies check passed"
}

# Clean build artifacts
clean_build() {
    if [[ $CLEAN == true ]]; then
        log_info "Cleaning build artifacts..."
        rm -rf $DIST_DIR/ $BUILD_DIR/wheels/ $BUILD_DIR/release/ $BUILD_DIR/debug/
        log_success "Build artifacts cleaned"
    fi
}

# Build for specific platforms
build_wheels() {
    log_info "Building wheels for platform: $PLATFORM"

    mkdir -p $DIST_DIR

    if [[ $DRY_RUN == true ]]; then
        log_warning "DRY RUN: Would build wheels for $PLATFORM"
        return
    fi

    case $PLATFORM in
        linux)
            log_info "Building for Linux platforms..."
            # Use maturin with different targets
            for target in x86_64-unknown-linux-gnu aarch64-unknown-linux-gnu i686-unknown-linux-gnu; do
                log_info "Building for $target..."
                maturin build --release --target $target --out $DIST_DIR || log_warning "Failed to build for $target"
            done
            ;;
        windows)
            if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
                log_info "Building for Windows platforms..."
                maturin build --release --target x86_64-pc-windows-msvc --out $DIST_DIR
                maturin build --release --target i686-pc-windows-msvc --out $DIST_DIR
            else
                log_warning "Windows builds require Windows environment or cross-compilation setup"
            fi
            ;;
        macos)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                log_info "Building for macOS platforms..."
                maturin build --release --target x86_64-apple-darwin --out $DIST_DIR
                maturin build --release --target aarch64-apple-darwin --out $DIST_DIR
            else
                log_warning "macOS builds require macOS environment or cross-compilation setup"
            fi
            ;;
        all|*)
            log_info "Building for current platform..."
            maturin build --release --out $DIST_DIR

            # Also build source distribution
            log_info "Building source distribution..."
            maturin sdist --out $DIST_DIR
            ;;
    esac

    log_success "Build completed"
    log_info "Built packages:"
    ls -la $DIST_DIR/ || log_warning "No packages found in $DIST_DIR/"
}

# Test the built package
test_package() {
    if [[ $SKIP_TEST == true ]]; then
        log_info "Skipping package testing"
        return
    fi

    log_info "Testing built package..."

    if [[ $DRY_RUN == true ]]; then
        log_warning "DRY RUN: Would test package installation"
        return
    fi

    # Find the most recent wheel
    WHEEL=$(ls -t $DIST_DIR/*.whl 2>/dev/null | head -n1)
    if [[ -z "$WHEEL" ]]; then
        log_warning "No wheel found to test"
        return
    fi

    log_info "Testing wheel: $(basename "$WHEEL")"

    # Create a temporary virtual environment
    TEMP_VENV=$(mktemp -d)
    python -m venv "$TEMP_VENV"

    # Activate virtual environment and test
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        source "$TEMP_VENV/Scripts/activate"
    else
        source "$TEMP_VENV/bin/activate"
    fi

    pip install --quiet --upgrade pip
    pip install --quiet "$WHEEL"

    # Test import
    python -c "import pyripgrep; print('Package import: ✅'); print(f'Module location: {pyripgrep.__file__}')"

    # Basic functionality test
    python -c "
import pyripgrep
import tempfile
import os

# Create a test file
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write('Hello World\\nTest Pattern\\nAnother line\\n')
    test_file = f.name

try:
    # Test basic search
    grep = pyripgrep.Grep()
    results = list(grep.search('Pattern', test_file))
    assert len(results) > 0, 'Search should find results'
    print('Basic search test: ✅')
finally:
    os.unlink(test_file)
"

    deactivate
    rm -rf "$TEMP_VENV"

    log_success "Package testing completed successfully"
}

# Publish to repository
publish_package() {
    local repo=$1
    local repo_name=$2
    local token_env=$3

    log_info "Publishing to $repo_name..."

    if [[ $DRY_RUN == true ]]; then
        log_warning "DRY RUN: Would publish to $repo_name"
        return
    fi

    # Check if token is available
    if [[ -z "${!token_env}" ]]; then
        log_error "$token_env environment variable is not set"
        log_info "Get your token from:"
        if [[ $repo == "testpypi" ]]; then
            log_info "  https://test.pypi.org/manage/account/token/"
        else
            log_info "  https://pypi.org/manage/account/token/"
        fi
        exit 1
    fi

    # Use maturin to upload
    if [[ $repo == "testpypi" ]]; then
        MATURIN_PYPI_TOKEN="${!token_env}" maturin upload --repository testpypi $DIST_DIR/*
    else
        MATURIN_PYPI_TOKEN="${!token_env}" maturin upload $DIST_DIR/*
    fi

    log_success "Successfully published to $repo_name"
}

# Main execution
main() {
    log_info "🚀 Starting $PROJECT_NAME build and publish process"
    log_info "Command: $COMMAND, Platform: $PLATFORM"

    check_dependencies
    clean_build
    build_wheels
    test_package

    case $COMMAND in
        build-only)
            log_success "Build completed. Packages are in $DIST_DIR/"
            ;;
        test)
            publish_package "testpypi" "TestPyPI" "TEST_PYPI_TOKEN"
            log_info "Test installation with: pip install -i https://test.pypi.org/simple/ $PROJECT_NAME"
            ;;
        prod)
            publish_package "pypi" "PyPI" "PYPI_TOKEN"
            log_info "Install with: pip install $PROJECT_NAME"
            ;;
    esac

    log_success "🎉 All done!"
}

# Run main function
main
