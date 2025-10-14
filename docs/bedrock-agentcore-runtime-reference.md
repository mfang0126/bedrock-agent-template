# AWS Bedrock AgentCore Runtime CLI Reference

> **Preview Release**: This API is in preview and subject to change.

## Overview

The `bedrock-agentcore` CLI provides data plane operations for interacting with AWS Bedrock AgentCore resources. This service enables runtime operations including agent invocation, memory management, session control, and authentication for running agents.

**Key Difference from Control Plane:**
- **bedrock-agentcore** (this document): Runtime operations - invoke agents, manage sessions, handle memory
- **bedrock-agentcore-control**: Infrastructure management - create/update runtimes, gateways, credential providers

## Installation

```bash
pip install awscli
aws configure  # Configure AWS credentials
```

Verify installation:
```bash
aws bedrock-agentcore help
```

---

## Command Categories

1. **Agent Runtime Invocation** - Execute agents and receive responses
2. **Memory Management** - Create, retrieve, update, and delete agent memory records
3. **Session Control** - Manage browser, code interpreter, and runtime sessions
4. **Authentication & Access** - Token management and authentication flows
5. **Event Management** - Create and manage conversational events
6. **Actor Management** - List and manage agent actors

---

## Agent Runtime Invocation

### invoke-agent-runtime

Sends a request to an agent or tool hosted in an AgentCore Runtime and receives responses in real-time.

**Syntax:**
```bash
aws bedrock-agentcore invoke-agent-runtime \
    --agent-runtime-arn <arn> \
    --payload <input-data> \
    <outfile> \
    [--content-type <mime-type>] \
    [--accept <mime-type>] \
    [--runtime-session-id <session-id>] \
    [--runtime-user-id <user-id>] \
    [--qualifier <version>] \
    [--mcp-session-id <mcp-session>] \
    [--trace-id <trace>] \
    [--trace-parent <parent>]
```

**Required Parameters:**

| Parameter | Description | Constraints |
|-----------|-------------|-------------|
| `--agent-runtime-arn` | ARN of the agent runtime | Valid ARN format |
| `--payload` | Input data to send to agent | 0-100,000,000 bytes |
| `<outfile>` | File to save response content | Valid file path |

**Optional Parameters:**

| Parameter | Description |
|-----------|-------------|
| `--content-type` | MIME type of input payload (e.g., application/json) |
| `--accept` | Desired MIME type for response |
| `--runtime-session-id` | Unique identifier for session continuity |
| `--runtime-user-id` | User identifier for user-specific context |
| `--qualifier` | Agent version or endpoint to invoke |
| `--mcp-session-id` | Model Context Protocol session ID |
| `--trace-id` | Distributed tracing identifier |
| `--trace-parent` | Parent trace context |

**Example - Simple Invocation:**
```bash
# Create input payload
cat > input.json <<EOF
{
  "query": "List all open issues in the repository",
  "repository": "owner/repo"
}
EOF

# Invoke agent runtime
aws bedrock-agentcore invoke-agent-runtime \
    --agent-runtime-arn arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/github-agent \
    --payload file://input.json \
    --content-type application/json \
    --accept application/json \
    response.json

# View response
cat response.json
```

**Example - Session-Based Invocation:**
```bash
# First invocation in session
aws bedrock-agentcore invoke-agent-runtime \
    --agent-runtime-arn arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/github-agent \
    --payload '{"query": "Create a new issue"}' \
    --runtime-session-id session-abc123 \
    --runtime-user-id user-mingfang \
    response1.json

# Follow-up invocation in same session
aws bedrock-agentcore invoke-agent-runtime \
    --agent-runtime-arn arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/github-agent \
    --payload '{"query": "What was the issue number?"}' \
    --runtime-session-id session-abc123 \
    --runtime-user-id user-mingfang \
    response2.json
```

**Example - Orchestrator Calling Another Agent:**
```python
import boto3
import json

client = boto3.client('bedrock-agentcore', region_name='ap-southeast-2')

# Orchestrator invokes GitHub agent
response = client.invoke_agent_runtime(
    agentRuntimeArn='arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/github-agent',
    payload=json.dumps({
        'action': 'create_issue',
        'repository': 'owner/repo',
        'title': 'Bug in authentication',
        'body': 'OAuth flow is failing for new users'
    }),
    contentType='application/json',
    accept='application/json',
    runtimeSessionId='orchestrator-session-123',
    runtimeUserId='orchestrator-agent'
)

# Process streaming response
result = b''
for event in response['response']:
    if 'chunk' in event:
        result += event['chunk']['bytes']

output = json.loads(result.decode('utf-8'))
print(f"Created issue: {output['issue_url']}")
```

**Response Structure:**
```json
{
    "runtimeSessionId": "session-abc123",
    "contentType": "application/json",
    "statusCode": 200,
    "response": "<streaming-blob>"
}
```

**Required IAM Permissions:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "bedrock-agentcore:InvokeAgentRuntime",
            "Resource": "arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/*"
        }
    ]
}
```

---

### get-agent-card

Retrieves metadata and configuration information about an agent.

**Syntax:**
```bash
aws bedrock-agentcore get-agent-card \
    --agent-runtime-arn <arn>
```

**Example:**
```bash
aws bedrock-agentcore get-agent-card \
    --agent-runtime-arn arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/github-agent
```

**Output:**
```json
{
    "agentCard": {
        "name": "github-agent",
        "description": "GitHub integration agent for repository management",
        "version": "1.0.0",
        "capabilities": [
            "repository_management",
            "issue_tracking",
            "pull_request_operations"
        ],
        "tools": [
            "list_repositories",
            "create_issue",
            "get_pull_request"
        ]
    }
}
```

---

## Memory Management

### batch-create-memory-records

Creates multiple memory records in a single batch operation.

**Syntax:**
```bash
aws bedrock-agentcore batch-create-memory-records \
    --memory-id <memory-id> \
    --records <record-list>
```

**Parameters:**

| Parameter | Description | Constraints |
|-----------|-------------|-------------|
| `--memory-id` | AgentCore Memory resource identifier | 12 characters, alphanumeric |
| `--records` | List of memory records to create | 0-100 records per batch |

**Record Structure:**
```json
{
    "requestIdentifier": "unique-request-id",
    "namespaces": ["category"],
    "content": {
        "text": "Memory record content"
    },
    "timestamp": "2024-10-15T10:30:00Z",
    "memoryStrategyId": "strategy-123"
}
```

**Example:**
```bash
# Create batch records file
cat > memory-records.json <<EOF
{
    "memoryId": "mem-abc123def456",
    "records": [
        {
            "requestIdentifier": "req-001",
            "namespaces": ["github"],
            "content": {
                "text": "User prefers detailed issue descriptions with code examples"
            },
            "timestamp": "2024-10-15T10:00:00Z"
        },
        {
            "requestIdentifier": "req-002",
            "namespaces": ["preferences"],
            "content": {
                "text": "Default repository: owner/main-project"
            },
            "timestamp": "2024-10-15T10:01:00Z"
        },
        {
            "requestIdentifier": "req-003",
            "namespaces": ["github", "workflow"],
            "content": {
                "text": "Automatically assign issues to mingfang"
            },
            "timestamp": "2024-10-15T10:02:00Z"
        }
    ]
}
EOF

# Batch create memory records
aws bedrock-agentcore batch-create-memory-records \
    --cli-input-json file://memory-records.json
```

**Output:**
```json
{
    "successfulRecords": [
        {
            "recordId": "rec-001",
            "memoryId": "mem-abc123def456",
            "requestIdentifier": "req-001",
            "createdAt": "2024-10-15T10:00:00Z"
        },
        {
            "recordId": "rec-002",
            "memoryId": "mem-abc123def456",
            "requestIdentifier": "req-002",
            "createdAt": "2024-10-15T10:01:00Z"
        },
        {
            "recordId": "rec-003",
            "memoryId": "mem-abc123def456",
            "requestIdentifier": "req-003",
            "createdAt": "2024-10-15T10:02:00Z"
        }
    ],
    "failedRecords": []
}
```

---

### retrieve-memory-records

Retrieves memory records based on query criteria.

**Syntax:**
```bash
aws bedrock-agentcore retrieve-memory-records \
    --memory-id <memory-id> \
    [--query-text <text>] \
    [--namespaces <namespace-list>] \
    [--max-results <number>]
```

**Example:**
```bash
# Retrieve GitHub-related memories
aws bedrock-agentcore retrieve-memory-records \
    --memory-id mem-abc123def456 \
    --namespaces github \
    --max-results 10
```

**Output:**
```json
{
    "records": [
        {
            "recordId": "rec-001",
            "content": {
                "text": "User prefers detailed issue descriptions with code examples"
            },
            "namespaces": ["github"],
            "timestamp": "2024-10-15T10:00:00Z",
            "score": 0.95
        }
    ]
}
```

---

### list-memory-records

Lists all memory records in a memory resource.

**Syntax:**
```bash
aws bedrock-agentcore list-memory-records \
    --memory-id <memory-id> \
    [--max-results <number>] \
    [--next-token <token>]
```

**Example:**
```bash
aws bedrock-agentcore list-memory-records \
    --memory-id mem-abc123def456 \
    --max-results 50
```

---

### get-memory-record

Retrieves a specific memory record by ID.

**Syntax:**
```bash
aws bedrock-agentcore get-memory-record \
    --memory-id <memory-id> \
    --record-id <record-id>
```

**Example:**
```bash
aws bedrock-agentcore get-memory-record \
    --memory-id mem-abc123def456 \
    --record-id rec-001
```

---

### batch-update-memory-records

Updates multiple memory records in a single batch operation.

**Syntax:**
```bash
aws bedrock-agentcore batch-update-memory-records \
    --memory-id <memory-id> \
    --records <updated-record-list>
```

**Example:**
```bash
cat > update-records.json <<EOF
{
    "memoryId": "mem-abc123def456",
    "records": [
        {
            "recordId": "rec-001",
            "content": {
                "text": "User prefers detailed issue descriptions with code examples and screenshots"
            }
        }
    ]
}
EOF

aws bedrock-agentcore batch-update-memory-records \
    --cli-input-json file://update-records.json
```

---

### batch-delete-memory-records

Deletes multiple memory records in a single batch operation.

**Syntax:**
```bash
aws bedrock-agentcore batch-delete-memory-records \
    --memory-id <memory-id> \
    --record-ids <record-id-list>
```

**Example:**
```bash
aws bedrock-agentcore batch-delete-memory-records \
    --memory-id mem-abc123def456 \
    --record-ids rec-001 rec-002 rec-003
```

---

### delete-memory-record

Deletes a single memory record.

**Syntax:**
```bash
aws bedrock-agentcore delete-memory-record \
    --memory-id <memory-id> \
    --record-id <record-id>
```

**Example:**
```bash
aws bedrock-agentcore delete-memory-record \
    --memory-id mem-abc123def456 \
    --record-id rec-001
```

---

## Session Control

### start-browser-session

Creates and initializes a browser session for web content interaction.

**Syntax:**
```bash
aws bedrock-agentcore start-browser-session \
    --browser-identifier <browser-id> \
    [--name <session-name>] \
    [--session-timeout-seconds <seconds>] \
    [--view-port width=<pixels>,height=<pixels>]
```

**Parameters:**

| Parameter | Description | Constraints |
|-----------|-------------|-------------|
| `--browser-identifier` | Browser resource identifier | Required |
| `--name` | Human-readable session name | Optional |
| `--session-timeout-seconds` | Session timeout | 60-28800 seconds (default: 3600) |
| `--view-port` | Browser viewport dimensions | width: 320-3840px, height: 240-2160px |

**Example:**
```bash
aws bedrock-agentcore start-browser-session \
    --browser-identifier browser-abc123 \
    --name "GitHub Issue Browser" \
    --session-timeout-seconds 1800 \
    --view-port width=1920,height=1080
```

**Output:**
```json
{
    "browserIdentifier": "browser-abc123",
    "sessionId": "browser-session-xyz789",
    "createdAt": "2024-10-15T10:30:00Z",
    "automationStream": {
        "endpoint": "wss://automation.bedrock.amazonaws.com/...",
        "status": "ACTIVE"
    },
    "liveViewStream": {
        "endpoint": "wss://liveview.bedrock.amazonaws.com/...",
        "status": "ACTIVE"
    }
}
```

**Use Cases:**
- Web scraping and data extraction
- Automated form filling
- Website testing and validation
- Visual inspection of web pages

---

### list-browser-sessions

Lists all active browser sessions.

**Syntax:**
```bash
aws bedrock-agentcore list-browser-sessions \
    --browser-identifier <browser-id> \
    [--max-results <number>] \
    [--next-token <token>]
```

**Example:**
```bash
aws bedrock-agentcore list-browser-sessions \
    --browser-identifier browser-abc123
```

---

### stop-browser-session

Terminates a browser session.

**Syntax:**
```bash
aws bedrock-agentcore stop-browser-session \
    --browser-identifier <browser-id> \
    --session-id <session-id>
```

**Example:**
```bash
aws bedrock-agentcore stop-browser-session \
    --browser-identifier browser-abc123 \
    --session-id browser-session-xyz789
```

---

### start-code-interpreter-session

Creates a code interpreter session for executing code.

**Syntax:**
```bash
aws bedrock-agentcore start-code-interpreter-session \
    --code-interpreter-identifier <interpreter-id> \
    [--name <session-name>] \
    [--session-timeout-seconds <seconds>]
```

**Example:**
```bash
aws bedrock-agentcore start-code-interpreter-session \
    --code-interpreter-identifier interpreter-abc123 \
    --name "Python Data Analysis Session" \
    --session-timeout-seconds 3600
```

**Output:**
```json
{
    "codeInterpreterIdentifier": "interpreter-abc123",
    "sessionId": "code-session-xyz789",
    "createdAt": "2024-10-15T10:30:00Z",
    "status": "READY"
}
```

---

### list-code-interpreter-sessions

Lists all code interpreter sessions.

**Syntax:**
```bash
aws bedrock-agentcore list-code-interpreter-sessions \
    --code-interpreter-identifier <interpreter-id>
```

---

### stop-code-interpreter-session

Terminates a code interpreter session.

**Syntax:**
```bash
aws bedrock-agentcore stop-code-interpreter-session \
    --code-interpreter-identifier <interpreter-id> \
    --session-id <session-id>
```

---

### list-sessions

Lists all sessions across all types.

**Syntax:**
```bash
aws bedrock-agentcore list-sessions \
    [--session-type <type>] \
    [--max-results <number>] \
    [--next-token <token>]
```

**Example:**
```bash
# List all sessions
aws bedrock-agentcore list-sessions

# List only browser sessions
aws bedrock-agentcore list-sessions \
    --session-type BROWSER
```

---

### stop-runtime-session

Stops a runtime session by session ID.

**Syntax:**
```bash
aws bedrock-agentcore stop-runtime-session \
    --session-id <session-id>
```

**Example:**
```bash
aws bedrock-agentcore stop-runtime-session \
    --session-id session-abc123
```

---

## Authentication & Access

### get-workload-access-token

Obtains a workload access token for agentic workloads not acting on behalf of a user.

**Syntax:**
```bash
aws bedrock-agentcore get-workload-access-token \
    --workload-name <workload-name>
```

**Parameters:**

| Parameter | Description | Constraints |
|-----------|-------------|-------------|
| `--workload-name` | Workload identifier | 3-255 characters, alphanumeric, underscore, period, hyphen |

**Example:**
```bash
# Orchestrator agent gets token for system operations
aws bedrock-agentcore get-workload-access-token \
    --workload-name orchestrator-agent
```

**Output:**
```json
{
    "workloadAccessToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Use Cases:**
- Agent-to-agent authentication
- System-level operations
- Background tasks without user context

---

### get-workload-access-token-for-user-id

Obtains a workload access token on behalf of a specific user.

**Syntax:**
```bash
aws bedrock-agentcore get-workload-access-token-for-user-id \
    --workload-name <workload-name> \
    --user-id <user-id>
```

**Example:**
```bash
aws bedrock-agentcore get-workload-access-token-for-user-id \
    --workload-name github-agent \
    --user-id user-mingfang
```

---

### get-workload-access-token-for-jwt

Obtains a workload access token using JWT authentication.

**Syntax:**
```bash
aws bedrock-agentcore get-workload-access-token-for-jwt \
    --workload-name <workload-name> \
    --jwt-token <jwt-token>
```

**Example:**
```bash
aws bedrock-agentcore get-workload-access-token-for-jwt \
    --workload-name github-agent \
    --jwt-token "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### get-resource-oauth2-token

Retrieves an OAuth2 access token for a resource.

**Syntax:**
```bash
aws bedrock-agentcore get-resource-oauth2-token \
    --credential-provider-id <provider-id> \
    --user-id <user-id>
```

**Example:**
```bash
aws bedrock-agentcore get-resource-oauth2-token \
    --credential-provider-id cp-github-oauth \
    --user-id user-mingfang
```

**Output:**
```json
{
    "accessToken": "gho_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "tokenType": "Bearer",
    "expiresIn": 3600,
    "refreshToken": "ghr_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "scope": "repo user"
}
```

---

### get-resource-api-key

Retrieves an API key for a resource.

**Syntax:**
```bash
aws bedrock-agentcore get-resource-api-key \
    --credential-provider-id <provider-id>
```

**Example:**
```bash
aws bedrock-agentcore get-resource-api-key \
    --credential-provider-id cp-github-api
```

---

### complete-resource-token-auth

Completes the OAuth2 authorization flow.

**Syntax:**
```bash
aws bedrock-agentcore complete-resource-token-auth \
    --credential-provider-id <provider-id> \
    --authorization-code <code> \
    --state <state> \
    --user-id <user-id>
```

**Example:**
```bash
aws bedrock-agentcore complete-resource-token-auth \
    --credential-provider-id cp-github-oauth \
    --authorization-code "abc123def456" \
    --state "random-state-string" \
    --user-id user-mingfang
```

---

## Event Management

### create-event

Creates a conversational event in agent memory.

**Syntax:**
```bash
aws bedrock-agentcore create-event \
    --memory-id <memory-id> \
    --actor-id <actor-id> \
    --event-timestamp <timestamp> \
    --payload <event-payload> \
    [--session-id <session-id>] \
    [--branch <branch-id>] \
    [--metadata <key-value-pairs>]
```

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `--memory-id` | AgentCore Memory resource identifier |
| `--actor-id` | Identifier for the event's actor |
| `--event-timestamp` | When the event occurred (ISO 8601 format) |
| `--payload` | Event content (conversational or blob) |
| `--session-id` | Session identifier for grouping events |
| `--branch` | Conversation thread/branch identifier |
| `--metadata` | Additional key-value metadata |

**Payload Types:**

1. **Conversational** (text-based with role):
```json
{
    "conversational": {
        "content": [
            {
                "text": "Please create an issue for the authentication bug"
            }
        ],
        "role": "USER"
    }
}
```

2. **Blob** (binary content):
```json
{
    "blob": {
        "contentType": "image/png",
        "data": "<base64-encoded-data>"
    }
}
```

**Roles:**
- `USER` - End user input
- `ASSISTANT` - Agent response
- `TOOL` - Tool execution result
- `OTHER` - Other system events

**Example - User Query:**
```bash
cat > event-user.json <<EOF
{
    "memoryId": "mem-abc123def456",
    "actorId": "user-mingfang",
    "eventTimestamp": "2024-10-15T10:30:00Z",
    "sessionId": "session-123",
    "payload": {
        "conversational": {
            "content": [
                {
                    "text": "Create a new issue titled 'Fix OAuth flow' in my repository"
                }
            ],
            "role": "USER"
        }
    },
    "metadata": {
        "source": "cli",
        "userAgent": "aws-cli/2.31.14"
    }
}
EOF

aws bedrock-agentcore create-event \
    --cli-input-json file://event-user.json
```

**Example - Assistant Response:**
```bash
cat > event-assistant.json <<EOF
{
    "memoryId": "mem-abc123def456",
    "actorId": "github-agent",
    "eventTimestamp": "2024-10-15T10:30:15Z",
    "sessionId": "session-123",
    "payload": {
        "conversational": {
            "content": [
                {
                    "text": "I've created issue #42 titled 'Fix OAuth flow' in your repository owner/repo. You can view it at https://github.com/owner/repo/issues/42"
                }
            ],
            "role": "ASSISTANT"
        }
    },
    "metadata": {
        "issueNumber": "42",
        "repository": "owner/repo",
        "issueUrl": "https://github.com/owner/repo/issues/42"
    }
}
EOF

aws bedrock-agentcore create-event \
    --cli-input-json file://event-assistant.json
```

**Example - Tool Execution:**
```bash
cat > event-tool.json <<EOF
{
    "memoryId": "mem-abc123def456",
    "actorId": "create-issue-tool",
    "eventTimestamp": "2024-10-15T10:30:10Z",
    "sessionId": "session-123",
    "branch": "issue-creation-flow",
    "payload": {
        "conversational": {
            "content": [
                {
                    "text": "Tool: create_issue\nInput: {\"title\": \"Fix OAuth flow\", \"repository\": \"owner/repo\"}\nResult: Issue #42 created successfully"
                }
            ],
            "role": "TOOL"
        }
    },
    "metadata": {
        "toolName": "create_issue",
        "executionTime": "5234ms",
        "status": "success"
    }
}
EOF

aws bedrock-agentcore create-event \
    --cli-input-json file://event-tool.json
```

**Output:**
```json
{
    "eventId": "event-xyz789",
    "memoryId": "mem-abc123def456",
    "createdAt": "2024-10-15T10:30:00Z"
}
```

---

### list-events

Lists events from agent memory.

**Syntax:**
```bash
aws bedrock-agentcore list-events \
    --memory-id <memory-id> \
    [--session-id <session-id>] \
    [--branch <branch-id>] \
    [--max-results <number>] \
    [--next-token <token>]
```

**Example:**
```bash
# List all events in a session
aws bedrock-agentcore list-events \
    --memory-id mem-abc123def456 \
    --session-id session-123

# List events in a specific conversation branch
aws bedrock-agentcore list-events \
    --memory-id mem-abc123def456 \
    --session-id session-123 \
    --branch issue-creation-flow
```

---

### get-event

Retrieves a specific event by ID.

**Syntax:**
```bash
aws bedrock-agentcore get-event \
    --memory-id <memory-id> \
    --event-id <event-id>
```

**Example:**
```bash
aws bedrock-agentcore get-event \
    --memory-id mem-abc123def456 \
    --event-id event-xyz789
```

---

### delete-event

Deletes an event from memory.

**Syntax:**
```bash
aws bedrock-agentcore delete-event \
    --memory-id <memory-id> \
    --event-id <event-id>
```

**Example:**
```bash
aws bedrock-agentcore delete-event \
    --memory-id mem-abc123def456 \
    --event-id event-xyz789
```

---

### update-browser-stream

Updates browser stream configuration.

**Syntax:**
```bash
aws bedrock-agentcore update-browser-stream \
    --browser-identifier <browser-id> \
    --session-id <session-id> \
    --stream-type <type> \
    --configuration <config>
```

**Example:**
```bash
aws bedrock-agentcore update-browser-stream \
    --browser-identifier browser-abc123 \
    --session-id browser-session-xyz789 \
    --stream-type LIVE_VIEW \
    --configuration '{
        "resolution": "1920x1080",
        "frameRate": 30
    }'
```

---

## Actor Management

### list-actors

Lists all actors in the agent system.

**Syntax:**
```bash
aws bedrock-agentcore list-actors \
    [--max-results <number>] \
    [--next-token <token>]
```

**Example:**
```bash
aws bedrock-agentcore list-actors --max-results 50
```

**Output:**
```json
{
    "actors": [
        {
            "actorId": "github-agent",
            "actorType": "AGENT",
            "name": "GitHub Agent",
            "description": "GitHub integration agent"
        },
        {
            "actorId": "user-mingfang",
            "actorType": "USER",
            "name": "Ming Fang"
        },
        {
            "actorId": "create-issue-tool",
            "actorType": "TOOL",
            "name": "Create Issue Tool"
        }
    ]
}
```

---

## Common Workflows

### 1. Complete Agent Invocation with Memory

```bash
# Step 1: Get workload access token
TOKEN=$(aws bedrock-agentcore get-workload-access-token-for-user-id \
    --workload-name github-agent \
    --user-id user-mingfang \
    --query 'workloadAccessToken' \
    --output text)

# Step 2: Create input event
cat > user-input-event.json <<EOF
{
    "memoryId": "mem-abc123def456",
    "actorId": "user-mingfang",
    "eventTimestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "sessionId": "session-$(uuidgen)",
    "payload": {
        "conversational": {
            "content": [{"text": "List all open issues"}],
            "role": "USER"
        }
    }
}
EOF

aws bedrock-agentcore create-event \
    --cli-input-json file://user-input-event.json

# Step 3: Invoke agent runtime
aws bedrock-agentcore invoke-agent-runtime \
    --agent-runtime-arn arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/github-agent \
    --payload '{"query": "List all open issues"}' \
    --runtime-session-id $SESSION_ID \
    --runtime-user-id user-mingfang \
    response.json

# Step 4: Create assistant response event
cat > assistant-response-event.json <<EOF
{
    "memoryId": "mem-abc123def456",
    "actorId": "github-agent",
    "eventTimestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "sessionId": "$SESSION_ID",
    "payload": {
        "conversational": {
            "content": [{"text": "$(cat response.json)"}],
            "role": "ASSISTANT"
        }
    }
}
EOF

aws bedrock-agentcore create-event \
    --cli-input-json file://assistant-response-event.json
```

---

### 2. Browser-Enabled Web Scraping

```bash
# Step 1: Start browser session
BROWSER_SESSION=$(aws bedrock-agentcore start-browser-session \
    --browser-identifier browser-abc123 \
    --name "GitHub Issues Scraper" \
    --session-timeout-seconds 1800 \
    --view-port width=1920,height=1080 \
    --query 'sessionId' \
    --output text)

# Step 2: Invoke agent with browser context
aws bedrock-agentcore invoke-agent-runtime \
    --agent-runtime-arn arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/github-agent \
    --payload "{
        \"action\": \"scrape_issues\",
        \"url\": \"https://github.com/owner/repo/issues\",
        \"browserSessionId\": \"$BROWSER_SESSION\"
    }" \
    response.json

# Step 3: Stop browser session
aws bedrock-agentcore stop-browser-session \
    --browser-identifier browser-abc123 \
    --session-id $BROWSER_SESSION
```

---

### 3. Multi-Agent Orchestration with Events

```bash
# Orchestrator receives user request and delegates to GitHub agent

# Step 1: Log orchestrator receives request
SESSION_ID="orchestrator-$(uuidgen)"

cat > orchestrator-receives.json <<EOF
{
    "memoryId": "mem-orchestrator-123",
    "actorId": "orchestrator-agent",
    "eventTimestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "sessionId": "$SESSION_ID",
    "payload": {
        "conversational": {
            "content": [{"text": "User requests: Create GitHub issue for bug"}],
            "role": "OTHER"
        }
    },
    "metadata": {
        "phase": "receive",
        "targetAgent": "github-agent"
    }
}
EOF

aws bedrock-agentcore create-event --cli-input-json file://orchestrator-receives.json

# Step 2: Orchestrator invokes GitHub agent
aws bedrock-agentcore invoke-agent-runtime \
    --agent-runtime-arn arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/github-agent \
    --payload '{
        "action": "create_issue",
        "title": "Authentication Bug",
        "body": "OAuth flow fails for new users"
    }' \
    --runtime-session-id github-session-$(uuidgen) \
    github-response.json

# Step 3: Log GitHub agent response
cat > github-responds.json <<EOF
{
    "memoryId": "mem-orchestrator-123",
    "actorId": "github-agent",
    "eventTimestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "sessionId": "$SESSION_ID",
    "payload": {
        "conversational": {
            "content": [{"text": "$(cat github-response.json)"}],
            "role": "ASSISTANT"
        }
    },
    "metadata": {
        "phase": "delegate_response",
        "sourceAgent": "github-agent"
    }
}
EOF

aws bedrock-agentcore create-event --cli-input-json file://github-responds.json

# Step 4: Orchestrator returns to user
# (Continue orchestration flow...)
```

---

### 4. Session-Based Conversation Flow

```python
#!/usr/bin/env python3
import boto3
import json
import uuid
from datetime import datetime

client = boto3.client('bedrock-agentcore', region_name='ap-southeast-2')
session_id = f"session-{uuid.uuid4()}"
memory_id = "mem-abc123def456"

def create_event(actor_id, content, role):
    """Create a conversational event"""
    return client.create_event(
        memoryId=memory_id,
        actorId=actor_id,
        eventTimestamp=datetime.utcnow().isoformat() + 'Z',
        sessionId=session_id,
        payload={
            'conversational': {
                'content': [{'text': content}],
                'role': role
            }
        }
    )

def invoke_agent(query):
    """Invoke agent and return response"""
    response = client.invoke_agent_runtime(
        agentRuntimeArn='arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/github-agent',
        payload=json.dumps({'query': query}),
        contentType='application/json',
        accept='application/json',
        runtimeSessionId=session_id,
        runtimeUserId='user-mingfang'
    )

    # Read streaming response
    result = b''
    for event in response['response']:
        if 'chunk' in event:
            result += event['chunk']['bytes']

    return json.loads(result.decode('utf-8'))

# Conversation flow
print(f"Session ID: {session_id}\n")

# Turn 1
user_query_1 = "List all open issues in my main repository"
print(f"User: {user_query_1}")
create_event('user-mingfang', user_query_1, 'USER')

agent_response_1 = invoke_agent(user_query_1)
print(f"Agent: {agent_response_1['response']}\n")
create_event('github-agent', agent_response_1['response'], 'ASSISTANT')

# Turn 2 (with context from previous turn)
user_query_2 = "Create a new issue for the first one you listed"
print(f"User: {user_query_2}")
create_event('user-mingfang', user_query_2, 'USER')

agent_response_2 = invoke_agent(user_query_2)
print(f"Agent: {agent_response_2['response']}\n")
create_event('github-agent', agent_response_2['response'], 'ASSISTANT')

# Turn 3 (with full conversation context)
user_query_3 = "What was the issue number?"
print(f"User: {user_query_3}")
create_event('user-mingfang', user_query_3, 'USER')

agent_response_3 = invoke_agent(user_query_3)
print(f"Agent: {agent_response_3['response']}\n")
create_event('github-agent', agent_response_3['response'], 'ASSISTANT')

# Retrieve full conversation history
events = client.list_events(
    memoryId=memory_id,
    sessionId=session_id
)

print("\n=== Full Conversation History ===")
for event in events['events']:
    print(f"{event['actorId']}: {event['payload']['conversational']['content'][0]['text']}")
```

---

## Best Practices

### 1. Session Management

**Use Consistent Session IDs:**
```bash
# Generate once per conversation
SESSION_ID="session-$(uuidgen)"

# Use throughout conversation
aws bedrock-agentcore invoke-agent-runtime \
    --runtime-session-id $SESSION_ID \
    ...
```

**Set Appropriate Timeouts:**
- Short interactions: 300-900 seconds
- Standard conversations: 900-3600 seconds
- Long-running tasks: 3600-28800 seconds

### 2. Memory Organization

**Use Namespaces for Categorization:**
```json
{
    "namespaces": ["github", "preferences"],
    "content": {"text": "User prefers detailed commit messages"}
}
```

**Structure Memory Records:**
- User preferences
- Conversation context
- Domain knowledge
- Tool execution history

### 3. Event Logging

**Log All Conversation Turns:**
- USER: User input
- ASSISTANT: Agent response
- TOOL: Tool execution
- OTHER: System events

**Include Rich Metadata:**
```json
{
    "metadata": {
        "repository": "owner/repo",
        "issueNumber": "42",
        "executionTime": "5234ms",
        "status": "success"
    }
}
```

### 4. Error Handling

```python
import boto3
from botocore.exceptions import ClientError

client = boto3.client('bedrock-agentcore')

try:
    response = client.invoke_agent_runtime(
        agentRuntimeArn='arn:aws:bedrock:...',
        payload=json.dumps(payload)
    )
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'ThrottlingException':
        # Implement exponential backoff
        time.sleep(2 ** retry_count)
    elif error_code == 'ValidationException':
        # Fix payload and retry
        pass
    elif error_code == 'ResourceNotFoundException':
        # Agent runtime doesn't exist
        pass
    else:
        # Unexpected error
        raise
```

### 5. Performance Optimization

**Batch Operations:**
```bash
# Instead of 100 individual creates
aws bedrock-agentcore batch-create-memory-records \
    --memory-id mem-abc123 \
    --records file://100-records.json
```

**Use Pagination:**
```bash
# Efficient pagination for large result sets
NEXT_TOKEN=""
while true; do
    RESPONSE=$(aws bedrock-agentcore list-memory-records \
        --memory-id mem-abc123 \
        --max-results 100 \
        ${NEXT_TOKEN:+--next-token $NEXT_TOKEN})

    # Process records...

    NEXT_TOKEN=$(echo $RESPONSE | jq -r '.nextToken // empty')
    [[ -z "$NEXT_TOKEN" ]] && break
done
```

### 6. Security

**Use Least Privilege IAM:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:InvokeAgentRuntime",
                "bedrock-agentcore:CreateEvent",
                "bedrock-agentcore:ListEvents"
            ],
            "Resource": [
                "arn:aws:bedrock:*:*:agent-runtime/github-agent",
                "arn:aws:bedrock:*:*:memory/mem-abc123*"
            ]
        }
    ]
}
```

**Validate User Input:**
- Sanitize payloads before invocation
- Validate session IDs
- Check authorization tokens

**Rotate Credentials:**
- Refresh OAuth tokens before expiry
- Update API keys regularly
- Use temporary credentials when possible

---

## Troubleshooting

### Common Issues

#### 1. Agent Invocation Timeout

**Problem:** Agent doesn't respond within timeout period

**Solutions:**
- Increase timeout in lifecycle configuration
- Optimize agent code for faster response
- Check network connectivity
- Review CloudWatch logs for errors

```bash
# Check agent runtime status
aws bedrock-agentcore-control get-agent-runtime \
    --agent-runtime-id abc123def456 \
    --query 'status'
```

---

#### 2. Memory Record Creation Fails

**Problem:** Batch create operation fails partially

**Solutions:**
- Check record size limits (16,000 characters)
- Validate JSON structure
- Reduce batch size
- Review failed records in response

```bash
# Smaller batches
aws bedrock-agentcore batch-create-memory-records \
    --memory-id mem-abc123 \
    --records file://small-batch.json
```

---

#### 3. Session Not Found

**Problem:** Runtime session ID not recognized

**Solutions:**
- Verify session was created successfully
- Check session hasn't timed out
- Use consistent session ID throughout conversation
- List active sessions to verify

```bash
# List active sessions
aws bedrock-agentcore list-sessions \
    --session-type RUNTIME
```

---

#### 4. Authentication Errors

**Problem:** Token or credential errors

**Solutions:**
- Refresh expired OAuth tokens
- Verify credential provider configuration
- Check IAM permissions
- Validate token format

```bash
# Get fresh token
aws bedrock-agentcore get-resource-oauth2-token \
    --credential-provider-id cp-github-oauth \
    --user-id user-mingfang
```

---

#### 5. Browser Session Failures

**Problem:** Browser session won't start or crashes

**Solutions:**
- Check browser resource exists
- Verify viewport dimensions are valid
- Reduce session timeout if resource constrained
- Review browser session logs

```bash
# List browser sessions
aws bedrock-agentcore list-browser-sessions \
    --browser-identifier browser-abc123

# Stop problematic session
aws bedrock-agentcore stop-browser-session \
    --browser-identifier browser-abc123 \
    --session-id browser-session-xyz789
```

---

## Cost Optimization

### 1. Session Lifecycle Management

```bash
# Stop unused sessions regularly
aws bedrock-agentcore list-sessions | \
    jq -r '.sessions[] | select(.lastActivityTime < (now - 3600)) | .sessionId' | \
    while read session_id; do
        aws bedrock-agentcore stop-runtime-session --session-id $session_id
    done
```

### 2. Memory Record Cleanup

```bash
# Delete old memory records
aws bedrock-agentcore list-memory-records \
    --memory-id mem-abc123 | \
    jq -r '.records[] | select(.timestamp < (now - 2592000)) | .recordId' | \
    xargs -n 50 | \
    while read -a record_ids; do
        aws bedrock-agentcore batch-delete-memory-records \
            --memory-id mem-abc123 \
            --record-ids ${record_ids[@]}
    done
```

### 3. Optimize Payload Sizes

- Compress large payloads
- Remove unnecessary data
- Use references instead of full content
- Paginate large result sets

### 4. Monitor Usage

- Track invocation counts via CloudWatch
- Set up billing alarms
- Use tagging for cost allocation
- Review usage patterns regularly

---

## Integration Patterns

### Python SDK (boto3)

```python
import boto3
import json

# Initialize client
client = boto3.client('bedrock-agentcore', region_name='ap-southeast-2')

# Invoke agent
response = client.invoke_agent_runtime(
    agentRuntimeArn='arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/github-agent',
    payload=json.dumps({'query': 'List issues'}),
    contentType='application/json',
    runtimeSessionId='session-123'
)

# Process streaming response
result = b''
for event in response['response']:
    if 'chunk' in event:
        result += event['chunk']['bytes']

output = json.loads(result.decode('utf-8'))
print(output)
```

### Shell Scripting

```bash
#!/bin/bash
set -euo pipefail

AGENT_ARN="arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/github-agent"
SESSION_ID="session-$(uuidgen)"

# Function to invoke agent
invoke_agent() {
    local query="$1"
    aws bedrock-agentcore invoke-agent-runtime \
        --agent-runtime-arn "$AGENT_ARN" \
        --payload "{\"query\": \"$query\"}" \
        --runtime-session-id "$SESSION_ID" \
        /tmp/response.json

    cat /tmp/response.json
}

# Usage
invoke_agent "List all issues"
invoke_agent "What was the first issue?"
```

---

## Related Documentation

- [Bedrock AgentCore Control Plane Reference](./bedrock-agentcore-control-reference.md)
- [AWS Bedrock User Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/)
- [AWS CLI Command Reference](https://docs.aws.amazon.com/cli/latest/reference/bedrock-agentcore/)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agentcore.html)
- [AgentCore Runtime Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-runtime.html)

---

## Quick Reference

### Essential Commands

```bash
# Invoke agent
aws bedrock-agentcore invoke-agent-runtime \
    --agent-runtime-arn <arn> \
    --payload <data> \
    response.json

# Create memory records
aws bedrock-agentcore batch-create-memory-records \
    --memory-id <id> \
    --records <records>

# Retrieve memories
aws bedrock-agentcore retrieve-memory-records \
    --memory-id <id> \
    --namespaces <namespaces>

# Create event
aws bedrock-agentcore create-event \
    --memory-id <id> \
    --actor-id <actor> \
    --event-timestamp <timestamp> \
    --payload <payload>

# List events
aws bedrock-agentcore list-events \
    --memory-id <id> \
    --session-id <session>

# Start browser session
aws bedrock-agentcore start-browser-session \
    --browser-identifier <id> \
    --session-timeout-seconds <seconds>

# Get access token
aws bedrock-agentcore get-workload-access-token \
    --workload-name <name>

# List sessions
aws bedrock-agentcore list-sessions
```

---

## Support and Feedback

For issues, questions, or feedback:
- AWS Support Console: https://console.aws.amazon.com/support/
- AWS Documentation: https://docs.aws.amazon.com/bedrock/
- AWS Forums: https://repost.aws/

**Note**: Amazon Bedrock AgentCore is in preview and subject to change. Always refer to the latest AWS documentation for the most current information.
