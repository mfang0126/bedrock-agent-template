# GitHub Agent - Technical Specification

## Overview
A production-ready AWS Bedrock AgentCore agent that authenticates with GitHub using OAuth 2.0 Device Flow and performs repository operations. Supports local CLI testing and AgentCore Runtime deployment.

## Architecture

### Dual-Mode Design
```
┌─────────────────────────────────────────────────────────┐
│                    github_agent                          │
├─────────────────────────────────────────────────────────┤
│  Local Mode          │          Production Mode          │
│  (CLI testing)       │       (AgentCore Runtime)         │
├──────────────────────┼───────────────────────────────────┤
│  __main__.py         │         runtime.py                │
│  (typer CLI)         │  (BedrockAgentCoreApp)            │
│        ↓             │            ↓                       │
│  ┌──────────────────────────────────────┐               │
│  │         agent.py (Strands)           │               │
│  │    Shared Core Agent Logic           │               │
│  └──────────────────────────────────────┘               │
│        ↓                      ↓                          │
│   auth.py              github_client.py                  │
│  (Device Flow)           (API Wrapper)                   │
│        ↓                      ↓                          │
│   config.py ────────────────────                        │
│  (Env Vars / Secrets Manager)                           │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
outbound_auth_github/
├── pyproject.toml              # uv + poethepoet configuration
├── .env.example                # Local credentials template
├── Dockerfile                  # ARM64 container for AgentCore
├── README.md                   # Setup & usage documentation
├── requirements.txt            # Auto-generated from pyproject.toml
├── src/
│   └── github_agent/
│       ├── __init__.py
│       ├── __main__.py         # CLI entry point (typer)
│       ├── runtime.py          # AgentCore Runtime entrypoint
│       ├── agent.py            # Core Strands agent logic (shared)
│       ├── auth.py             # GitHub Device Flow OAuth
│       ├── github_client.py    # GitHub API client wrapper
│       └── config.py           # Configuration management
└── tests/
    └── test_agent.py           # Basic agent tests
```

## Technology Stack

### Core Dependencies
- **Python**: 3.10+
- **Package Manager**: `uv`
- **Task Runner**: `poethepoet`
- **Agent Framework**: `strands-agents`
- **Runtime**: `bedrock-agentcore`
- **Model**: Claude 3.7 Sonnet (`us.anthropic.claude-3-7-sonnet-20250219-v1:0`)
- **HTTP Client**: `httpx`
- **CLI Framework**: `typer`
- **Config**: `python-dotenv`
- **AWS SDK**: `boto3>=1.39.15`

### pyproject.toml Configuration

```toml
[project]
name = "github-agent"
version = "0.1.0"
description = "AWS Bedrock AgentCore agent with GitHub OAuth"
requires-python = ">=3.10"
dependencies = [
    "bedrock-agentcore[strands-agents]>=0.1.0",
    "strands-agents>=0.1.0",
    "httpx>=0.27.0",
    "typer>=0.12.0",
    "python-dotenv>=1.0.0",
    "boto3>=1.39.15",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project.scripts]
github-agent = "github_agent.__main__:app"

[tool.poe.tasks]
agent = "python -m github_agent"
auth = "python -m github_agent auth"
invoke = "python -m github_agent invoke"
test = "pytest tests/"
build = "docker build -t github-agent:latest ."
```

## Component Specifications

### 1. CLI Interface (`__main__.py`)

**Purpose**: Local testing and development interface using typer

**Commands**:
- Simple: `github-agent invoke "list my repos"`
- Structured: `github-agent agent run "list repos"`
- Auth test: `github-agent auth`
- Tools list: `github-agent tools list`

**Implementation Pattern**:
```python
import typer
from .agent import GitHubAgent
from .auth import GitHubDeviceFlow
from .config import Config

app = typer.Typer()

@app.command()
def invoke(prompt: str):
    """Simple invocation"""
    config = Config(environment="local")
    agent = GitHubAgent(config)
    result = agent.run(prompt)
    print(result)

@app.command()
def auth():
    """Test OAuth Device Flow"""
    config = Config(environment="local")
    flow = GitHubDeviceFlow(config.get_github_credentials()["client_id"])
    # Device flow implementation
```

### 2. AgentCore Runtime (`runtime.py`)

**Purpose**: Production entrypoint for AgentCore Runtime deployment

**Implementation Pattern**:
```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from .agent import create_agent
from .config import Config

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    """Process AgentCore invocations"""
    config = Config(environment="production")
    agent = create_agent(config)

    user_input = payload.get("prompt", "")
    response = agent(user_input)

    return {"result": response.message}

if __name__ == "__main__":
    app.run()
```

### 3. Agent Core (`agent.py`)

**Purpose**: Shared Strands agent logic for both CLI and Runtime

**Implementation Pattern**:
```python
from strands import Agent, tool
from strands.models import BedrockModel
from .github_client import GitHubClient
from .auth import github_access_token

@tool
def inspect_github_repos() -> str:
    """List user's GitHub repositories"""
    if not github_access_token:
        return "Authentication required"

    client = GitHubClient(github_access_token)
    return client.list_repos()

def create_agent(config):
    """Factory function for agent creation"""
    model = BedrockModel(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    )

    return Agent(
        model=model,
        tools=[inspect_github_repos],
        system_prompt="You are a GitHub assistant that helps users manage repositories."
    )
```

### 4. Authentication (`auth.py`)

**Purpose**: GitHub OAuth 2.0 Device Flow implementation

**Device Flow Steps**:
1. Request device code from GitHub
2. Display user code and verification URL
3. Poll GitHub token endpoint
4. Store access token

**Implementation Pattern**:
```python
import httpx
import time
from typing import Optional

github_access_token: Optional[str] = None

class GitHubDeviceFlow:
    BASE_URL = "https://github.com/login"

    def __init__(self, client_id: str):
        self.client_id = client_id

    def start_flow(self) -> dict:
        """Step 1: Request device code"""
        response = httpx.post(
            f"{self.BASE_URL}/device/code",
            headers={"Accept": "application/json"},
            data={
                "client_id": self.client_id,
                "scope": "repo read:user"
            }
        )
        return response.json()

    def poll_for_token(self, device_code: str, interval: int = 5) -> str:
        """Step 2-3: Poll for access token"""
        while True:
            response = httpx.post(
                f"{self.BASE_URL}/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": self.client_id,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                }
            )
            data = response.json()

            if "access_token" in data:
                global github_access_token
                github_access_token = data["access_token"]
                return github_access_token

            if "error" in data and data["error"] == "authorization_pending":
                time.sleep(interval)
                continue

            raise Exception(f"OAuth error: {data.get('error', 'Unknown')}")
```

**AgentCore Integration** (for production):
```python
from bedrock_agentcore.identity.auth import requires_access_token

@requires_access_token(
    provider_name="github-provider",
    scopes=["repo", "read:user"],
    auth_flow="USER_FEDERATION",
    force_authentication=True,
)
async def get_github_token(*, access_token: str) -> str:
    global github_access_token
    github_access_token = access_token
    return access_token
```

### 5. GitHub Client (`github_client.py`)

**Purpose**: GitHub API wrapper using httpx

**Implementation Pattern**:
```python
import httpx
from typing import List, Dict

class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(self, access_token: str):
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

    def get_user(self) -> Dict:
        """Get authenticated user info"""
        with httpx.Client() as client:
            response = client.get(f"{self.BASE_URL}/user", headers=self.headers)
            response.raise_for_status()
            return response.json()

    def list_repos(self) -> str:
        """List user's repositories"""
        user = self.get_user()
        username = user.get("login")

        with httpx.Client() as client:
            response = client.get(
                f"{self.BASE_URL}/search/repositories?q=user:{username}",
                headers=self.headers
            )
            response.raise_for_status()
            repos = response.json().get("items", [])

            result = [f"Repositories for {username}:"]
            for repo in repos:
                result.append(f"📁 {repo['name']} - ⭐ {repo['stargazers_count']}")
                if repo.get("description"):
                    result.append(f"   {repo['description']}")

            return "\n".join(result)
```

### 6. Configuration (`config.py`)

**Purpose**: Environment-aware credential management

**Implementation Pattern**:
```python
import os
import boto3
import json
from typing import Dict
from dotenv import load_dotenv

class Config:
    def __init__(self, environment: str = "local"):
        self.environment = environment

        if environment == "local":
            load_dotenv()

    def get_github_credentials(self) -> Dict[str, str]:
        """Get GitHub OAuth credentials based on environment"""
        if self.environment == "local":
            return {
                "client_id": os.getenv("GITHUB_CLIENT_ID"),
                "client_secret": os.getenv("GITHUB_CLIENT_SECRET")
            }
        else:
            return self._get_from_secrets_manager()

    def _get_from_secrets_manager(self) -> Dict[str, str]:
        """Fetch credentials from AWS Secrets Manager (production)"""
        client = boto3.client('secretsmanager', region_name='us-east-1')
        secret_name = "github-agent/credentials"

        try:
            response = client.get_secret_value(SecretId=secret_name)
            secret = json.loads(response['SecretString'])

            return {
                "client_id": secret['client_id'],
                "client_secret": secret['client_secret']
            }
        except Exception as e:
            print(f"Error fetching secrets: {e}")
            raise
```

## Deployment Workflows

### Local Development
```bash
# Setup
git clone <repo>
cd outbound_auth_github
uv sync
cp .env.example .env
# Edit .env with GitHub OAuth credentials

# Test authentication
uv run poe auth

# Run agent
uv run poe invoke "list my repositories"

# Alternative: Direct CLI
uv run github-agent invoke "show my repos"
```

### AgentCore Runtime Deployment

**Prerequisites**:
1. GitHub OAuth App credentials in AWS Secrets Manager
2. ECR repository for container image
3. AgentCore Runtime environment configured

**Deployment Steps**:
```bash
# Build ARM64 container
uv run poe build

# Tag and push to ECR
docker tag github-agent:latest <account>.dkr.ecr.us-east-1.amazonaws.com/github-agent:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/github-agent:latest

# Deploy to AgentCore Runtime (using AWS CLI or SDK)
aws bedrock-agentcore create-agent \
    --agent-name github-agent \
    --runtime-image <ecr-image-uri> \
    --execution-role-arn <role-arn>
```

## Environment Variables

### Local Development (`.env`)
```env
GITHUB_CLIENT_ID=<your-github-oauth-app-client-id>
GITHUB_CLIENT_SECRET=<your-github-oauth-app-client-secret>
```

### Production (AWS Secrets Manager)
**Secret Name**: `github-agent/credentials`
**Secret Structure**:
```json
{
  "client_id": "<github-oauth-app-client-id>",
  "client_secret": "<github-oauth-app-client-secret>"
}
```

## GitHub OAuth App Setup

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Create new OAuth App:
   - **Application name**: GitHub Agent
   - **Homepage URL**: `https://your-domain.com`
   - **Authorization callback URL**: (Not used for Device Flow)
3. Enable Device Flow authorization
4. Copy Client ID and Client Secret

## Logging & Error Handling

**Approach**: Basic print statements (as per requirements)

```python
# Simple logging pattern
def invoke(prompt: str):
    print(f"User input: {prompt}")
    try:
        result = agent(prompt)
        print(f"Result: {result}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        raise
```

## Testing Strategy

```python
# tests/test_agent.py
import pytest
from github_agent.agent import create_agent
from github_agent.config import Config

def test_agent_creation():
    config = Config(environment="local")
    agent = create_agent(config)
    assert agent is not None

def test_github_client():
    # Mock httpx responses
    pass
```

## Security Considerations

1. **Never hardcode credentials** - use environment variables or Secrets Manager
2. **Token handling** - use `@requires_access_token` decorator in production
3. **IAM permissions** - Lambda execution role needs `secretsmanager:GetSecretValue`
4. **Scopes** - Request minimal GitHub scopes (`repo`, `read:user`)

## Performance & Scalability

- **AgentCore Runtime**: Serverless, auto-scales up to 8-hour sessions
- **HTTP Client**: httpx with connection pooling
- **Model**: Claude 3.7 Sonnet (hardcoded, production-grade)

## Future Enhancements (Out of Scope)

- Advanced logging (structured logging, CloudWatch integration)
- Multiple GitHub operations (issues, PRs, commits)
- Session persistence with AgentCore Memory
- Retry logic and exponential backoff
- Comprehensive test coverage

## References

- [AWS Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/)
- [GitHub Device Flow OAuth](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow)
- [Strands Agents Framework](https://strandsagents.com/)
- [AWS Bedrock AgentCore Samples](https://github.com/awslabs/amazon-bedrock-agentcore-samples)
