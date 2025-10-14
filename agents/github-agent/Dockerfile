FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app

# Environment variables for Python and AWS
ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DOCKER_CONTAINER=1 \
    AWS_REGION=ap-southeast-2 \
    AWS_DEFAULT_REGION=ap-southeast-2

# Copy agent files (respecting .dockerignore)
COPY . .

# Install dependencies from pyproject.toml
RUN uv pip install .

# Create non-root user for security
RUN useradd -m -u 1000 bedrock_agentcore && \
    chown -R bedrock_agentcore:bedrock_agentcore /app

USER bedrock_agentcore

# Expose ports for AgentCore runtime
EXPOSE 9000
EXPOSE 8000
EXPOSE 8080

# Run the agent runtime
CMD ["python", "-m", "src.runtime"]
