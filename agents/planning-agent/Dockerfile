FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app

# All environment variables in one layer
ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DOCKER_CONTAINER=1 \
    AWS_REGION=ap-southeast-2 \
    AWS_DEFAULT_REGION=ap-southeast-2 \
    BEDROCK_AGENTCORE_MEMORY_ID=planning_mem-qrcXY02YXi \
    BEDROCK_AGENTCORE_MEMORY_NAME=planning_mem



COPY . .
# Install from pyproject.toml directory
RUN cd . && uv pip install .





# Set AWS region environment variable

ENV AWS_REGION=ap-southeast-2
ENV AWS_DEFAULT_REGION=ap-southeast-2


# Signal that this is running in Docker for host binding logic
ENV DOCKER_CONTAINER=1

# Create non-root user
RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

EXPOSE 9000
EXPOSE 8000
EXPOSE 8080

# Copy entire project (respecting .dockerignore)
COPY . .

# Use the full module path

CMD ["python", "-m", "src.runtime"]
