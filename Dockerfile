# Multi-platform Docker build for ripgrep-python
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install maturin
RUN pip install maturin

# Set working directory
WORKDIR /app

# Copy source code
COPY . .

# Build stage for different architectures
FROM base as builder

# Build wheel
RUN maturin build --release --out dist

# Final stage
FROM python:3.11-slim as final

# Copy built wheel
COPY --from=builder /app/dist/*.whl /tmp/

# Install the wheel
RUN pip install /tmp/*.whl && rm /tmp/*.whl

# Test installation
RUN python -c "import pyripgrep; print('✅ Package installed successfully')"

# Set default command
CMD ["python", "-c", "import pyripgrep; print('ripgrep-python is ready!')"]
