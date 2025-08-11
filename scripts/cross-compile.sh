#!/bin/bash

# cross-compile.sh - Cross-compilation script for multiple platforms
# This script helps set up cross-compilation for different targets

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Supported targets
LINUX_TARGETS=(
    "x86_64-unknown-linux-gnu"
    "aarch64-unknown-linux-gnu"
    "i686-unknown-linux-gnu"
    "armv7-unknown-linux-gnueabihf"
    "s390x-unknown-linux-gnu"
    "powerpc64le-unknown-linux-gnu"
)

WINDOWS_TARGETS=(
    "x86_64-pc-windows-msvc"
    "i686-pc-windows-msvc"
)

MACOS_TARGETS=(
    "x86_64-apple-darwin"
    "aarch64-apple-darwin"
)

install_target() {
    local target=$1
    log_info "Installing Rust target: $target"
    rustup target add $target
}

setup_cross_compilation() {
    log_info "Setting up cross-compilation environment..."

    # Install cross if not available
    if ! command -v cross &> /dev/null; then
        log_info "Installing cross..."
        cargo install cross
    fi

    # Install common targets
    log_info "Installing common Rust targets..."

    case "$OSTYPE" in
        linux*)
            for target in "${LINUX_TARGETS[@]}" "${WINDOWS_TARGETS[@]}" "${MACOS_TARGETS[@]}"; do
                install_target $target 2>/dev/null || log_warning "Failed to install $target"
            done
            ;;
        darwin*)
            for target in "${MACOS_TARGETS[@]}" "${LINUX_TARGETS[@]}"; do
                install_target $target 2>/dev/null || log_warning "Failed to install $target"
            done
            ;;
        msys*|cygwin*)
            for target in "${WINDOWS_TARGETS[@]}" "${LINUX_TARGETS[@]}"; do
                install_target $target 2>/dev/null || log_warning "Failed to install $target"
            done
            ;;
    esac

    log_success "Cross-compilation setup complete"
}

build_for_target() {
    local target=$1
    local output_dir=${2:-dist}

    log_info "Building for target: $target"

    mkdir -p $output_dir

    # Try using cross first, fall back to maturin
    if command -v cross &> /dev/null && [[ $target == *"linux"* ]]; then
        log_info "Using cross for $target"
        cross build --release --target $target
        # Note: cross doesn't directly build Python wheels, this is for Rust compilation
    fi

    # Use maturin for Python wheel building
    maturin build --release --target $target --out $output_dir 2>/dev/null || {
        log_warning "Failed to build wheel for $target, skipping..."
        return 1
    }

    log_success "Built wheel for $target"
}

build_all_platforms() {
    local output_dir=${1:-dist}

    log_info "Building for all supported platforms..."

    mkdir -p $output_dir

    # Determine which targets to build based on host OS
    local targets_to_build=()

    case "$OSTYPE" in
        linux*)
            targets_to_build+=("${LINUX_TARGETS[@]}")
            log_info "Building Linux targets on Linux host"
            ;;
        darwin*)
            targets_to_build+=("${MACOS_TARGETS[@]}")
            log_info "Building macOS targets on macOS host"
            ;;
        msys*|cygwin*)
            targets_to_build+=("${WINDOWS_TARGETS[@]}")
            log_info "Building Windows targets on Windows host"
            ;;
    esac

    # Build for each target
    local built_count=0
    for target in "${targets_to_build[@]}"; do
        if build_for_target $target $output_dir; then
            ((built_count++))
        fi
    done

    log_success "Built wheels for $built_count targets"

    # Also build source distribution
    log_info "Building source distribution..."
    maturin sdist --out $output_dir

    log_info "All packages built:"
    ls -la $output_dir/
}

show_help() {
    cat << EOF
Cross-compilation helper for ripgrep-python

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    setup           Install cross-compilation tools and targets
    build TARGET    Build for specific target
    build-all       Build for all supported targets on current platform
    list-targets    List all supported targets
    help            Show this help

Examples:
    $0 setup
    $0 build x86_64-unknown-linux-gnu
    $0 build-all
    $0 list-targets

Supported targets:
  Linux:   ${LINUX_TARGETS[*]}
  Windows: ${WINDOWS_TARGETS[*]}
  macOS:   ${MACOS_TARGETS[*]}
EOF
}

list_targets() {
    log_info "Supported targets:"
    echo
    echo "Linux targets:"
    for target in "${LINUX_TARGETS[@]}"; do
        echo "  - $target"
    done
    echo
    echo "Windows targets:"
    for target in "${WINDOWS_TARGETS[@]}"; do
        echo "  - $target"
    done
    echo
    echo "macOS targets:"
    for target in "${MACOS_TARGETS[@]}"; do
        echo "  - $target"
    done
}

# Main execution
case "${1:-help}" in
    setup)
        setup_cross_compilation
        ;;
    build)
        if [[ -z "$2" ]]; then
            log_error "Please specify a target to build for"
            show_help
            exit 1
        fi
        build_for_target "$2" "${3:-dist}"
        ;;
    build-all)
        build_all_platforms "${2:-dist}"
        ;;
    list-targets)
        list_targets
        ;;
    help|*)
        show_help
        ;;
esac
