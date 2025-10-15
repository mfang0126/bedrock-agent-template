# Agent Invocation Guide

Complete guide for invoking deployed agents in both CLIENT and AGENT modes.

## Quick Reference

### CLIENT Mode (Human Users)
```python
import boto3

client = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-2')

response = client.invoke_agent(
    agentId='your-agent-id',
    agentAliasId='TSTALIASID',
    sessionId='user-session-123',
    inputText='List my repositories'  # Just the prompt, no special markers
)

# Streams human-readable text with emojis and progress
for event in response['completion']:
    if 'chunk' in event:
        print(event['chunk']['bytes'].decode(), end='', flush=True)
```

### AGENT Mode (Agent-to-Agent)
```python
import boto3
import json

client = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-2')

# Add A2A markers to payload
payload = {
    "prompt": "List my repositories",
    "_agent_call": True,
    "source_agent": "orchestrator"
}

response = client.invoke_agent(
    agentId='your-agent-id',
    agentAliasId='TSTALIASID',
    sessionId='agent-session-123',
    inputText=json.dumps(payload)  # Serialize with A2A markers
)

# Returns structured JSON
result = json.loads(response['output'])
# {"success": true, "message": "...", "data": {...}, "agent_type": "github"}
```

---

## Mode Detection

Agents automatically detect communication mode based on payload structure:

### CLIENT Mode Triggers
```python
# Simple text prompt (default)
inputText = "List my repositories"

# JSON without A2A markers
inputText = json.dumps({"prompt": "List my repositories"})
```

**Result**: Streaming text responses, emojis, human-readable progress

### AGENT Mode Triggers
```python
# JSON with _agent_call marker
inputText = json.dumps({
    "prompt": "List my repositories",
    "_agent_call": True
})

# JSON with source_agent marker
inputText = json.dumps({
    "prompt": "List my repositories",
    "source_agent": "orchestrator"
})

# Custom User-Agent header
headers = {"user-agent": "agent2agent/1.0"}
```

**Result**: Single structured JSON response with data

---

## CLIENT Mode Invocation

### 1. Python (boto3)

```python
import boto3

def invoke_agent_client_mode(agent_id: str, prompt: str, session_id: str):
    """Invoke agent in CLIENT mode for human interaction."""

    client = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-2')

    response = client.invoke_agent(
        agentId=agent_id,
        agentAliasId='TSTALIASID',
        sessionId=session_id,
        inputText=prompt  # Plain text or JSON without A2A markers
    )

    # Stream responses
    full_response = ""
    for event in response.get('completion', []):
        if 'chunk' in event:
            chunk = event['chunk']['bytes'].decode('utf-8')
            print(chunk, end='', flush=True)
            full_response += chunk

    return full_response

# Example usage
response = invoke_agent_client_mode(
    agent_id='github-agent-xxxxx',
    prompt='List my repositories',
    session_id='user-alice-session-1'
)
```

### 2. AWS CLI

```bash
# Simple prompt
aws bedrock-agent-runtime invoke-agent \
    --agent-id github-agent-xxxxx \
    --agent-alias-id TSTALIASID \
    --session-id user-session-123 \
    --input-text "List my repositories" \
    --region ap-southeast-2 \
    response.json

# View streaming output
cat response.json
```

### 3. AgentCore CLI (Local/Deployed)

```bash
# Local testing
cd agents/github-agent
agentcore invoke '{"prompt": "List my repositories"}'

# Deployed agent
agentcore invoke \
    --agent-id github-agent-xxxxx \
    --session-id user-session-123 \
    "List my repositories"
```

### 4. Shell Scripts (Project Scripts)

```bash
# GitHub Agent
./invoke_github.sh "List my repositories"

# JIRA Agent
./invoke_jira.sh "List my projects"
```

---

## AGENT Mode Invocation (A2A)

### 1. Python (boto3)

```python
import boto3
import json

def invoke_agent_a2a_mode(
    agent_id: str,
    prompt: str,
    source_agent: str,
    session_id: str
) -> dict:
    """Invoke agent in AGENT mode for A2A communication."""

    client = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-2')

    # Create A2A payload
    payload = {
        "prompt": prompt,
        "_agent_call": True,
        "source_agent": source_agent
    }

    response = client.invoke_agent(
        agentId=agent_id,
        agentAliasId='TSTALIASID',
        sessionId=session_id,
        inputText=json.dumps(payload)  # Serialize with markers
    )

    # Parse structured response
    result_text = ""
    for event in response.get('completion', []):
        if 'chunk' in event:
            result_text += event['chunk']['bytes'].decode('utf-8')

    # Parse JSON response
    return json.loads(result_text)

# Example usage
result = invoke_agent_a2a_mode(
    agent_id='github-agent-xxxxx',
    prompt='List repositories',
    source_agent='orchestrator',
    session_id='agent-orchestrator-session-1'
)

print(result['success'])      # True
print(result['message'])      # "Listed 5 repositories"
print(result['data'])         # {"repositories": [...]}
print(result['agent_type'])   # "github"
```

### 2. From Orchestrator Agent

```python
# Inside orchestrator agent runtime.py
async def call_github_agent(prompt: str) -> dict:
    """Call GitHub agent from orchestrator."""

    import boto3
    import json

    client = boto3.client('bedrock-agent-runtime')

    # A2A payload
    payload = {
        "prompt": prompt,
        "_agent_call": True,
        "source_agent": "orchestrator"
    }

    response = client.invoke_agent(
        agentId=os.getenv('GITHUB_AGENT_ID'),
        agentAliasId='TSTALIASID',
        sessionId=f"orchestrator-{session_id}",
        inputText=json.dumps(payload)
    )

    # Parse structured response
    result = ""
    for event in response['completion']:
        if 'chunk' in event:
            result += event['chunk']['bytes'].decode('utf-8')

    return json.loads(result)
```

### 3. AWS CLI (A2A)

```bash
# Create A2A payload file
cat > a2a_payload.json <<EOF
{
  "prompt": "List repositories",
  "_agent_call": true,
  "source_agent": "orchestrator"
}
EOF

# Invoke with A2A payload
aws bedrock-agent-runtime invoke-agent \
    --agent-id github-agent-xxxxx \
    --agent-alias-id TSTALIASID \
    --session-id agent-session-123 \
    --input-text file://a2a_payload.json \
    --region ap-southeast-2 \
    response.json
```

---

## Response Formats

### CLIENT Mode Response

**Stream Output**:
```
🔐 Authenticating with GitHub...
✅ GitHub authentication successful

📂 Fetching repositories...

Repository 1: awesome-project
  ⭐ 42 stars
  🔨 Last updated: 2 days ago

Repository 2: cool-library
  ⭐ 128 stars
  🔨 Last updated: 1 week ago

✅ Found 2 repositories
```

**Characteristics**:
- Streaming text chunks
- Emojis for visual clarity
- Real-time progress indicators
- Human-readable format
- Natural language responses

### AGENT Mode Response

**JSON Output**:
```json
{
  "success": true,
  "message": "Listed 2 repositories successfully",
  "data": {
    "repositories": [
      {
        "name": "awesome-project",
        "stars": 42,
        "updated_at": "2024-10-13T10:30:00Z"
      },
      {
        "name": "cool-library",
        "stars": 128,
        "updated_at": "2024-10-08T15:45:00Z"
      }
    ],
    "count": 2
  },
  "agent_type": "github",
  "timestamp": "2024-10-15T12:30:00.000000",
  "metadata": {
    "command": "list_repositories",
    "execution_time_ms": 1234
  }
}
```

**Characteristics**:
- Single JSON response
- Structured data fields
- Machine-parseable format
- Success/failure indicators
- Agent type identification
- Timestamp for tracking

---

## Session Management

### SESSION IDs

**CLIENT Mode** - Use user-specific sessions:
```python
session_id = f"user-{user_id}-{timestamp}"
# Example: "user-alice-1697456789"
```

**AGENT Mode** - Use agent-specific sessions:
```python
session_id = f"agent-{source_agent}-{timestamp}"
# Example: "agent-orchestrator-1697456789"
```

### Session Lifecycle

```python
# Create session
session_id = f"user-alice-{int(time.time())}"

# Multiple calls in same session
invoke_agent(agent_id, "List repositories", session_id)
invoke_agent(agent_id, "Show details of first repo", session_id)
invoke_agent(agent_id, "Create an issue", session_id)

# Sessions persist for 8 hours on AgentCore
# After 8 hours, create new session
```

---

## Complete Examples

### Example 1: Web Application Integration

```python
from flask import Flask, request, jsonify
import boto3
import uuid

app = Flask(__name__)
bedrock = boto3.client('bedrock-agent-runtime', region_name='ap-southeast-2')

GITHUB_AGENT_ID = 'github-agent-xxxxx'

@app.route('/api/github/query', methods=['POST'])
def github_query():
    """CLIENT mode endpoint for web users."""

    user_id = request.json.get('user_id')
    prompt = request.json.get('prompt')

    # Generate user session ID
    session_id = f"webapp-user-{user_id}-{uuid.uuid4().hex[:8]}"

    # Invoke in CLIENT mode (plain prompt)
    response = bedrock.invoke_agent(
        agentId=GITHUB_AGENT_ID,
        agentAliasId='TSTALIASID',
        sessionId=session_id,
        inputText=prompt  # No A2A markers
    )

    # Stream response
    full_response = ""
    for event in response['completion']:
        if 'chunk' in event:
            full_response += event['chunk']['bytes'].decode('utf-8')

    return jsonify({
        "response": full_response,
        "session_id": session_id
    })

if __name__ == '__main__':
    app.run(debug=True)
```

### Example 2: Multi-Agent Orchestrator

```python
import boto3
import json

class AgentOrchestrator:
    """Orchestrator for A2A communication."""

    def __init__(self):
        self.client = boto3.client('bedrock-agent-runtime')
        self.agents = {
            'github': 'github-agent-xxxxx',
            'jira': 'jira-agent-xxxxx'
        }

    def call_agent(self, agent_name: str, prompt: str) -> dict:
        """Call specialized agent in AGENT mode."""

        # A2A payload with markers
        payload = {
            "prompt": prompt,
            "_agent_call": True,
            "source_agent": "orchestrator"
        }

        response = self.client.invoke_agent(
            agentId=self.agents[agent_name],
            agentAliasId='TSTALIASID',
            sessionId=f"orchestrator-{agent_name}-{int(time.time())}",
            inputText=json.dumps(payload)
        )

        # Parse structured response
        result = ""
        for event in response['completion']:
            if 'chunk' in event:
                result += event['chunk']['bytes'].decode('utf-8')

        return json.loads(result)

    def workflow_create_issue_from_repo(self, repo_name: str, issue_title: str):
        """Multi-agent workflow."""

        # Step 1: Get repo details from GitHub agent
        github_result = self.call_agent(
            'github',
            f"Get details of repository {repo_name}"
        )

        if not github_result['success']:
            return {"error": "Failed to get repo details"}

        # Step 2: Create JIRA issue
        jira_result = self.call_agent(
            'jira',
            f"Create issue: {issue_title} - From repo {repo_name}"
        )

        return {
            "github": github_result,
            "jira": jira_result
        }

# Usage
orchestrator = AgentOrchestrator()
result = orchestrator.workflow_create_issue_from_repo(
    "my-awesome-repo",
    "Bug: Login form validation"
)
```

---

## Troubleshooting

### Issue: Getting A2A Response in CLIENT Mode

**Problem**: Expecting streaming text but getting JSON.

**Solution**: Remove A2A markers from payload:
```python
# Wrong (triggers AGENT mode)
inputText = json.dumps({"prompt": "...", "_agent_call": True})

# Correct (triggers CLIENT mode)
inputText = "List repositories"
# OR
inputText = json.dumps({"prompt": "List repositories"})  # No _agent_call
```

### Issue: Getting Streaming Text in AGENT Mode

**Problem**: Expecting JSON but getting streaming text.

**Solution**: Add A2A markers to payload:
```python
# Wrong (triggers CLIENT mode)
inputText = "List repositories"

# Correct (triggers AGENT mode)
payload = {"prompt": "List repositories", "_agent_call": True}
inputText = json.dumps(payload)
```

### Issue: Cannot Parse Response

**Problem**: Response format doesn't match expected structure.

**Solution**: Check mode detection:
```python
import json

# Send test payload
payload = {"prompt": "what mode are you in?", "_agent_call": True}
response = invoke_agent(agent_id, json.dumps(payload), session_id)

# Check response type
if response.startswith('{'):
    print("AGENT mode (JSON)")
else:
    print("CLIENT mode (text stream)")
```

---

## Best Practices

### For CLIENT Mode (Human Users)

1. ✅ **Use descriptive prompts**: "List my repositories with stars"
2. ✅ **Session per user**: One session per user conversation
3. ✅ **Stream output**: Display real-time progress to users
4. ✅ **Handle emojis**: Ensure UI supports emoji rendering
5. ✅ **User-friendly session IDs**: `user-{user_id}-{timestamp}`

### For AGENT Mode (A2A)

1. ✅ **Always include markers**: `_agent_call: True` or `source_agent`
2. ✅ **Parse JSON responses**: Expect structured data
3. ✅ **Check success field**: `result['success']` before using data
4. ✅ **Handle errors gracefully**: Check for error fields in response
5. ✅ **Agent-specific session IDs**: `agent-{source}-{timestamp}`

### Security

1. ✅ **Validate session IDs**: Ensure users can only access their sessions
2. ✅ **Use IAM roles**: Don't embed credentials in code
3. ✅ **Rate limiting**: Implement request throttling
4. ✅ **Input validation**: Sanitize user inputs before sending to agents
5. ✅ **Audit logs**: Log all agent invocations for security

---

## Related Documentation

- [TESTING.md](TESTING.md) - Local testing guide
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment instructions
- [docs/Multi-Agent-Workflow.md](docs/Multi-Agent-Workflow.md) - Architecture details
- [docs/Progress-Streaming-Protocol.md](docs/Progress-Streaming-Protocol.md) - Streaming protocol

---

**Last Updated**: 2024-10-15
**Version**: 1.0.0
**Agents Covered**: All agents (coding, planning, orchestrator, github, jira)
