FROM python:3.11-slim

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Install system dependencies (e.g., for psycopg2)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install the project and its dependencies
RUN uv pip install --system -e .

# Expose the Streamlit port
EXPOSE 8501

# Default command starts the AI Agent UI
CMD ["ravioli", "agent"]
