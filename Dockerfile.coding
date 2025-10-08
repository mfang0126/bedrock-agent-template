# Multi-agent platform Dockerfile - Coding Agent
# Based on proven GitHub Agent template

FROM public.ecr.aws/docker/library/python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml README.md ./

# Install Python dependencies
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -e ".[strands-agents]"

# Install OpenTelemetry for instrumentation
RUN pip install --no-cache-dir opentelemetry-distro opentelemetry-exporter-otlp
RUN opentelemetry-bootstrap -a install

# Copy project files
# .dockerignore controls what gets copied
COPY . .

# Expose port for AgentCore
EXPOSE 8000

# Coding Agent specific entrypoint
CMD ["opentelemetry-instrument", "python", "-m", "src.agents.coding_agent.runtime"]
