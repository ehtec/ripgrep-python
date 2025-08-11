#!/bin/bash

# docker-build.sh - Docker-based multi-platform build script

set -e

PLATFORMS="linux/amd64,linux/arm64"
IMAGE_NAME="ripgrep-python-builder"
DIST_DIR="dist-docker"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }

show_help() {
    cat << EOF
Docker-based multi-platform build for ripgrep-python

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    setup       Set up Docker buildx for multi-platform builds
    build       Build wheels using Docker for multiple platforms
    extract     Extract wheels from Docker containers
    clean       Clean up Docker resources
    help        Show this help

Options:
    --platforms PLATFORMS    Comma-separated list of platforms (default: linux/amd64,linux/arm64)
    --output DIR            Output directory for wheels (default: dist-docker)

Examples:
    $0 setup
    $0 build --platforms linux/amd64,linux/arm64
    $0 extract --output dist-docker
EOF
}

setup_buildx() {
    log_info "Setting up Docker buildx for multi-platform builds..."

    # Create a new builder instance
    docker buildx create --name multiplatform-builder --use || true
    docker buildx inspect --bootstrap

    log_success "Docker buildx setup complete"
}

build_multiplatform() {
    local platforms=${1:-$PLATFORMS}
    local output_dir=${2:-$DIST_DIR}

    log_info "Building for platforms: $platforms"

    # Build for multiple platforms
    docker buildx build \
        --platform $platforms \
        --target builder \
        --output type=local,dest=$output_dir \
        .

    log_success "Multi-platform build complete"
    log_info "Wheels available in: $output_dir"
}

extract_wheels() {
    local output_dir=${1:-$DIST_DIR}

    log_info "Extracting wheels from Docker containers..."

    mkdir -p $output_dir

    # Find and copy wheels
    find $output_dir -name "*.whl" -exec cp {} $output_dir/ \;

    log_info "Extracted wheels:"
    ls -la $output_dir/*.whl 2>/dev/null || log_info "No wheels found"
}

clean_docker() {
    log_info "Cleaning up Docker resources..."

    # Remove builder
    docker buildx rm multiplatform-builder || true

    # Clean up images
    docker system prune -f

    log_success "Docker cleanup complete"
}

# Parse arguments
COMMAND=${1:-help}
PLATFORMS_ARG=""
OUTPUT_ARG=""

shift || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --platforms)
            PLATFORMS_ARG="$2"
            shift 2
            ;;
        --output)
            OUTPUT_ARG="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Execute command
case $COMMAND in
    setup)
        setup_buildx
        ;;
    build)
        build_multiplatform "${PLATFORMS_ARG:-$PLATFORMS}" "${OUTPUT_ARG:-$DIST_DIR}"
        ;;
    extract)
        extract_wheels "${OUTPUT_ARG:-$DIST_DIR}"
        ;;
    clean)
        clean_docker
        ;;
    help|*)
        show_help
        ;;
esac
