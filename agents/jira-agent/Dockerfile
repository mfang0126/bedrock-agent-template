FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app

# Copy agent files
COPY . .

# All environment variables in one layer
ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DOCKER_CONTAINER=1 \
    AWS_REGION=ap-southeast-2 \
    AWS_DEFAULT_REGION=ap-southeast-2 \
    JIRA_URL=https://kookaburra.atlassian.net

# Install dependencies
RUN uv pip install .

# Create non-root user AFTER installation and set ownership
RUN useradd -m -u 1000 bedrock_agentcore && \
    chown -R bedrock_agentcore:bedrock_agentcore /app

USER bedrock_agentcore

EXPOSE 9000
EXPOSE 8000
EXPOSE 8080

CMD ["python", "-m", "src.runtime"]