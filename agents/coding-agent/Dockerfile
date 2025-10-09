FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app

# All environment variables in one layer
ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DOCKER_CONTAINER=1 \
    AWS_REGION=ap-southeast-2 \
    AWS_DEFAULT_REGION=ap-southeast-2

# Copy project files
COPY . .

# Install dependencies
RUN cd . && uv pip install .

# Create workspace directory
RUN mkdir -p /tmp/workspaces && chmod 755 /tmp/workspaces

# Set environment variables
ENV WORKSPACE_BASE_PATH="/tmp/workspaces"
ENV MAX_FILE_SIZE="10485760"
ENV DEFAULT_TIMEOUT="30"
ENV MAX_TIMEOUT="300"

# Create non-root user
RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

# Expose port
EXPOSE 9000
EXPOSE 8000
EXPOSE 8080

# Use the full module path
CMD ["python", "-m", "src.runtime"]