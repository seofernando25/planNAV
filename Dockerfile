# Use a Python 3.14 base image
FROM python:3.14-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Copy only the files needed for installing dependencies to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Install dependencies without the project itself
RUN uv sync --frozen --no-install-project --no-dev

# --- Final Stage ---
FROM python:3.14-slim

WORKDIR /app

# Copy uv from the builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the environment and application code from the builder
COPY --from=builder /app/.venv /app/.venv
COPY . .

# Ensure we use the virtualenv
ENV PATH="/app/.venv/bin:$PATH"

# Create a non-root user for security
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app

# Create .cache directory for static files
RUN mkdir -p /app/.cache && chown -R appuser:appuser /app/.cache

USER appuser

# Expose the default FastAPI port
EXPOSE 8000

# Run the application
# We use the absolute path to python in the venv
CMD ["python", "run.py"]
