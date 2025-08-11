# Makefile for ripgrep-python cross-platform build and publish

.PHONY: help clean build test publish-test publish-prod setup-cross docker-setup all

# Default target
help:
	@echo "ripgrep-python build and publish commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev         - Build and install for development"
	@echo "  make test-local  - Run local tests"
	@echo "  make clean       - Clean build artifacts"
	@echo ""
	@echo "Building:"
	@echo "  make build       - Build wheel for current platform"
	@echo "  make build-all   - Build wheels for all platforms"
	@echo "  make setup-cross - Setup cross-compilation tools"
	@echo ""
	@echo "Docker builds:"
	@echo "  make docker-setup   - Setup Docker buildx"
	@echo "  make docker-build   - Build using Docker"
	@echo ""
	@echo "Publishing:"
	@echo "  make publish-test - Publish to TestPyPI"
	@echo "  make publish-prod - Publish to PyPI"
	@echo ""
	@echo "Utilities:"
	@echo "  make check-deps  - Check required dependencies"
	@echo "  make lint        - Run code linting"
	@echo "  make format      - Format code"

# Variables
DIST_DIR := dist
SCRIPTS_DIR := scripts
PLATFORM := all

# Development
dev:
	maturin develop

test-local:
	python -m pytest tests/ -v

clean:
	rm -rf $(DIST_DIR)/ target/wheels/ target/release/ target/debug/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

# Building
build:
	@echo "Building for current platform..."
	maturin build --release --out $(DIST_DIR)

build-all:
	@echo "Building for all platforms..."
	./$(SCRIPTS_DIR)/cross-compile.sh build-all $(DIST_DIR)

setup-cross:
	@echo "Setting up cross-compilation..."
	./$(SCRIPTS_DIR)/cross-compile.sh setup

# Docker builds
docker-setup:
	./$(SCRIPTS_DIR)/docker-build.sh setup

docker-build: docker-setup
	./$(SCRIPTS_DIR)/docker-build.sh build --output $(DIST_DIR)

# Publishing
publish-test: build
	@echo "Publishing to TestPyPI..."
	@if [ -z "$(TEST_PYPI_TOKEN)" ]; then \
		echo "❌ TEST_PYPI_TOKEN environment variable not set"; \
		echo "Get your token from: https://test.pypi.org/manage/account/token/"; \
		exit 1; \
	fi
	MATURIN_PYPI_TOKEN=$(TEST_PYPI_TOKEN) maturin upload --repository testpypi $(DIST_DIR)/*

publish-prod: build
	@echo "Publishing to PyPI..."
	@if [ -z "$(PYPI_TOKEN)" ]; then \
		echo "❌ PYPI_TOKEN environment variable not set"; \
		echo "Get your token from: https://pypi.org/manage/account/token/"; \
		exit 1; \
	fi
	MATURIN_PYPI_TOKEN=$(PYPI_TOKEN) maturin upload $(DIST_DIR)/*

# Full build and publish workflow
publish-test-full: clean build-all
	@./$(SCRIPTS_DIR)/publish.sh test

publish-prod-full: clean build-all
	@./$(SCRIPTS_DIR)/publish.sh prod

# Utilities
check-deps:
	@echo "Checking dependencies..."
	@command -v rustc >/dev/null 2>&1 || { echo "❌ Rust not installed"; exit 1; }
	@command -v python >/dev/null 2>&1 || { echo "❌ Python not installed"; exit 1; }
	@python -c "import maturin" 2>/dev/null || { echo "❌ Maturin not installed. Run: pip install maturin"; exit 1; }
	@echo "✅ All dependencies check passed"

lint:
	@echo "Running Rust linting..."
	cargo clippy --all-targets --all-features -- -D warnings
	@echo "Running Python linting..."
	@command -v ruff >/dev/null 2>&1 && ruff check . || echo "ruff not installed, skipping Python lint"

format:
	@echo "Formatting Rust code..."
	cargo fmt
	@echo "Formatting Python code..."
	@command -v ruff >/dev/null 2>&1 && ruff format . || echo "ruff not installed, skipping Python format"

# Version management
version:
	@grep '^version = ' pyproject.toml | head -1 | sed 's/version = "/Current version: /' | sed 's/"//'

bump-patch:
	@echo "Use ./scripts/publish.sh to manage versions"

bump-minor:
	@echo "Use ./scripts/publish.sh to manage versions"

# Release workflow
release-test: clean build
	@./scripts/publish.sh test

release-prod: clean build
	@./scripts/publish.sh prod
