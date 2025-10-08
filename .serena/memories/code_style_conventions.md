# Code Style & Conventions

## Python Standards
- **Version**: Python 3.10+ (type hints required)
- **Style**: Standard Python (PEP 8 compatible)
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Type Hints**: Used throughout (encouraged but not enforced)
- **Docstrings**: Present for major functions, Google-style format

## Project-Specific Patterns

### Tool Definition Pattern
```python
from strands import tool

@tool
def tool_name(param: str) -> str:
    """Brief description.
    
    Args:
        param: Parameter description
        
    Returns:
        Result description
    """
    # Access global token if needed
    if not github_access_token:
        return "Authentication required"
    
    # Make API call
    # Return string result
```

### Authentication Pattern
```python
# Global token variable at module level
github_access_token: Optional[str] = None

# AgentCore decorator for production
@requires_access_token(
    provider_name="github-provider",
    scopes=["repo", "read:user"],
    auth_flow='USER_FEDERATION',
    on_auth_url=on_auth_url,
    force_authentication=True,
)
async def get_github_access_token(*, access_token: str) -> str:
    global github_access_token
    github_access_token = access_token
    return access_token
```

### Runtime Entry Point Pattern
```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@app.entrypoint
def strands_agent_github(payload):
    """Process AgentCore invocations."""
    response = agent(payload.get("prompt"))
    return {"result": response.message}
```

### Error Handling
- Simple print statements for logging (as per requirements)
- Return error strings from tools (don't raise exceptions)
- Raise exceptions only for critical failures

### Import Organization
1. Standard library
2. Third-party packages
3. Local imports (relative)

## Comments
- Docstrings for public functions
- Inline comments for complex logic only
- No TODOs in committed code
- Clear function/variable names preferred over comments
