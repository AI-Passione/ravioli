FROM python:3.11-slim

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Install system dependencies (e.g., for psycopg2)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install the project and its dependencies
# Install project in editable mode with dev dependencies for testing
RUN uv pip install --system --extra dev -e .

# Expose the API port
EXPOSE 8000

# Default command starts the FastAPI backend
CMD ["uvicorn", "ravioli.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
