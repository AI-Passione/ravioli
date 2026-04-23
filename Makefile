.PHONY: up down setup ingest transform agent db-init

# Start services
up:
	@echo "Starting Docker services..."
	docker-compose -f docker/docker-compose.yml up -d
	@echo "Checking Ollama..."
	@ollama pull qwen2.5:3b
	@echo "Jimwurst is ready!"

# Stop services
down:
	docker-compose -f docker/docker-compose.yml down

# Setup environment
setup:
	uv pip install -e .
	@if [ ! -f docker/.env ]; then cp docker/.env.example docker/.env; fi
	@echo "Setup complete. Use 'jimwurst' command or 'make' targets."

# Ingestion targets (wrappers around CLI)
ingest-apple-health:
	uv run jimwurst ingest apple-health

ingest-spotify:
	uv run jimwurst ingest spotify

ingest-linkedin:
	uv run jimwurst ingest linkedin

ingest-substack:
	uv run jimwurst ingest substack

# Transformation
transform:
	uv run jimwurst transform

# Start Agent
agent:
	uv run jimwurst agent

# Init DB
db-init:
	uv run jimwurst db-init
