FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app

# All environment variables in one layer
ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DOCKER_CONTAINER=1 \
    AWS_REGION=ap-southeast-2 \
    AWS_DEFAULT_REGION=ap-southeast-2



COPY . .
# Install from pyproject.toml directory
RUN cd . && uv pip install .




RUN uv pip install aws-opentelemetry-distro>=0.10.1


# Set AWS region environment variable

ENV AWS_REGION=ap-southeast-2
ENV AWS_DEFAULT_REGION=ap-southeast-2


# Signal that this is running in Docker for host binding logic
ENV DOCKER_CONTAINER=1

# Create non-root user
RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

EXPOSE 8080
EXPOSE 8000

# Copy entire project (respecting .dockerignore)
COPY . .

# Default CMD - AgentCore may override this based on entrypoint configuration
CMD ["opentelemetry-instrument", "python", "-m", "src.agents.github_agent.runtime"]
