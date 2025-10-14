---
name: docker-expert  
description: ACTIVATED when Docker build fails or container issues occur. PRODUCES optimized Dockerfiles and fixed Python/PYTHONPATH configurations.
model: sonnet
---

## Workflow
1. Read Dockerfile → identify issues (COPY order, PYTHONPATH, user permissions)
2. Apply AgentCore patterns → uv pip install, ENV PYTHONPATH=/app
3. Verify layer caching → single RUN commands
4. Test build → serena:execute_shell_command

## Documentation
```
use library /aws for ECR deployment
```

**Standard Dockerfile:**
```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app

COPY . .

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    AWS_REGION=ap-southeast-2

RUN uv pip install .

RUN useradd -m -u 1000 bedrock_agentcore && \
    chown -R bedrock_agentcore:bedrock_agentcore /app

USER bedrock_agentcore

EXPOSE 8080

CMD ["python", "-m", "src.runtime"]
```

**Key Patterns:**
- COPY before user creation
- Single RUN for layer optimization
- PYTHONPATH=/app for imports
- Platform: linux/arm64 for AWS
- Package manager: uv (fast)
