# Multi-agent platform Dockerfile - Orchestrator Agent
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

# Set environment variables for sub-agent ARNs
ENV AWS_REGION=ap-southeast-2
ENV GITHUB_AGENT_ARN=arn:aws:bedrock-agentcore:ap-southeast-2:670326884047:runtime/runtime-08tk23FYi7
ENV PLANNING_AGENT_ARN=arn:aws:bedrock-agentcore:ap-southeast-2:670326884047:runtime/planning_agent-HOo1EJ7KvE
ENV JIRA_AGENT_ARN=arn:aws:bedrock-agentcore:ap-southeast-2:670326884047:runtime/jira_agent-WboCCb8qfb
ENV CODING_AGENT_ARN=arn:aws:bedrock-agentcore:ap-southeast-2:670326884047:runtime/coding_agent-sQJDwfGL8y

# Orchestrator Agent specific entrypoint
CMD ["opentelemetry-instrument", "python", "-m", "src.agents.orchestrator_agent.runtime"]
