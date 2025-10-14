# AWS Bedrock AgentCore Control CLI Reference

> **Preview Release**: This API is in preview and subject to change.

## Overview

The `bedrock-agentcore-control` CLI provides control plane operations for managing AWS Bedrock AgentCore resources. This service allows you to create, configure, modify, and monitor agent runtimes, gateways, credential providers, and other AgentCore infrastructure.

## Pre-use

When use it it have to start with "aws_use mingfang &&" in order to load the aws token.

```bash
aws_use mingfang && aws bedrock-agentcore-control ....
```

---

## Command Categories

1. **Agent Runtime Management** - Create and manage agent execution environments
2. **Gateway Management** - Configure API gateways for agent access
3. **Credential Providers** - Manage authentication (API keys, OAuth2)
4. **Browser Management** - Control browser instances for agents
5. **Resource Tagging** - Organize and categorize resources
6. **Monitoring** - Wait for resource state changes

---

## Agent Runtime Management

### create-agent-runtime

Creates a new AgentCore Runtime instance.

**Syntax:**

```bash
aws bedrock-agentcore-control create-agent-runtime \
    --agent-runtime-name <name> \
    --agent-runtime-artifact <artifact-config> \
    --role-arn <iam-role-arn> \
    --network-configuration <network-config> \
    [--description <text>] \
    [--authorizer-configuration <auth-config>] \
    [--request-header-configuration <header-config>] \
    [--protocol-configuration <protocol-config>] \
    [--lifecycle-configuration <lifecycle-config>] \
    [--environment-variables <env-vars>] \
    [--tags <tags>] \
    [--client-token <token>]
```

**Required Parameters:**

| Parameter                  | Description                          | Format                                |
| -------------------------- | ------------------------------------ | ------------------------------------- |
| `--agent-runtime-name`     | Unique name for the runtime          | Pattern: `[a-zA-Z][a-zA-Z0-9_]{0,47}` |
| `--agent-runtime-artifact` | Container configuration with ECR URI | JSON object                           |
| `--role-arn`               | IAM role ARN for runtime permissions | ARN string                            |
| `--network-configuration`  | Network settings (PUBLIC or VPC)     | JSON object                           |

**Optional Parameters:**

| Parameter                        | Description                                     |
| -------------------------------- | ----------------------------------------------- |
| `--description`                  | Human-readable description                      |
| `--authorizer-configuration`     | JWT authorization settings                      |
| `--request-header-configuration` | Allowed HTTP headers list                       |
| `--protocol-configuration`       | Communication protocol settings                 |
| `--lifecycle-configuration`      | Session timeout and max lifetime                |
| `--environment-variables`        | Runtime environment variables (key-value pairs) |
| `--tags`                         | Resource tags for organization                  |
| `--client-token`                 | Idempotency token                               |

**Example:**

```bash
aws bedrock-agentcore-control create-agent-runtime \
    --agent-runtime-name github-agent \
    --agent-runtime-artifact '{
        "containerConfiguration": {
            "containerUri": "123456789012.dkr.ecr.ap-southeast-2.amazonaws.com/github-agent:latest"
        }
    }' \
    --role-arn arn:aws:iam::123456789012:role/AgentRuntimeRole \
    --network-configuration '{
        "networkMode": "VPC",
        "networkModeConfig": {
            "securityGroups": ["sg-0123456789abcdef0"],
            "subnets": ["subnet-0123456789abcdef0", "subnet-0123456789abcdef1"]
        }
    }' \
    --description "GitHub integration agent runtime" \
    --lifecycle-configuration '{
        "sessionTimeoutMinutes": 30,
        "maxLifetimeMinutes": 120
    }' \
    --environment-variables '{
        "LOG_LEVEL": "INFO",
        "AWS_REGION": "ap-southeast-2"
    }' \
    --tags Key=Environment,Value=Production Key=Project,Value=MultiAgent
```

**Output:**

```json
{
  "agentRuntimeArn": "arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/github-agent",
  "agentRuntimeId": "abc123def456",
  "agentRuntimeVersion": "1",
  "workloadIdentityDetails": {
    "principalArn": "arn:aws:sts::123456789012:assumed-role/AgentRuntimeRole/github-agent"
  },
  "createdAt": "2024-10-15T10:30:00.000Z",
  "status": "CREATING"
}
```

---

### list-agent-runtimes

Lists all agent runtimes in your account.

**Syntax:**

```bash
aws bedrock-agentcore-control list-agent-runtimes \
    [--starting-token <token>] \
    [--page-size <number>] \
    [--max-items <number>]
```

**Parameters:**

| Parameter          | Description                             |
| ------------------ | --------------------------------------- |
| `--starting-token` | Pagination token from previous response |
| `--page-size`      | Number of items per service call        |
| `--max-items`      | Maximum total items to return           |

**Example:**

```bash
# List all agent runtimes
aws bedrock-agentcore-control list-agent-runtimes

# List with pagination
aws bedrock-agentcore-control list-agent-runtimes \
    --page-size 10 \
    --max-items 50
```

**Output:**

```json
{
  "agentRuntimes": [
    {
      "agentRuntimeArn": "arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/github-agent",
      "agentRuntimeId": "abc123def456",
      "agentRuntimeVersion": "1",
      "name": "github-agent",
      "description": "GitHub integration agent runtime",
      "status": "READY",
      "lastUpdatedAt": "2024-10-15T10:35:00.000Z"
    },
    {
      "agentRuntimeArn": "arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/coding-agent",
      "agentRuntimeId": "def456ghi789",
      "agentRuntimeVersion": "2",
      "name": "coding-agent",
      "description": "Code generation agent runtime",
      "status": "READY",
      "lastUpdatedAt": "2024-10-14T15:20:00.000Z"
    }
  ],
  "nextToken": "eyJsYXN0RXZhbHVhdGVkS2V5Ijp7Im5hbWUiOiJjb2RpbmctYWdlbnQifX0="
}
```

---

### get-agent-runtime

Retrieves detailed information about a specific agent runtime.

**Syntax:**

```bash
aws bedrock-agentcore-control get-agent-runtime \
    --agent-runtime-id <runtime-id>
```

**Example:**

```bash
aws bedrock-agentcore-control get-agent-runtime \
    --agent-runtime-id abc123def456
```

**Output:**

```json
{
  "agentRuntimeArn": "arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/github-agent",
  "agentRuntimeId": "abc123def456",
  "agentRuntimeVersion": "1",
  "name": "github-agent",
  "description": "GitHub integration agent runtime",
  "status": "READY",
  "roleArn": "arn:aws:iam::123456789012:role/AgentRuntimeRole",
  "networkConfiguration": {
    "networkMode": "VPC",
    "networkModeConfig": {
      "securityGroups": ["sg-0123456789abcdef0"],
      "subnets": ["subnet-0123456789abcdef0", "subnet-0123456789abcdef1"]
    }
  },
  "lifecycleConfiguration": {
    "sessionTimeoutMinutes": 30,
    "maxLifetimeMinutes": 120
  },
  "environmentVariables": {
    "LOG_LEVEL": "INFO",
    "AWS_REGION": "ap-southeast-2"
  },
  "createdAt": "2024-10-15T10:30:00.000Z",
  "lastUpdatedAt": "2024-10-15T10:35:00.000Z"
}
```

---

### update-agent-runtime

Updates an existing agent runtime configuration.

**Syntax:**

```bash
aws bedrock-agentcore-control update-agent-runtime \
    --agent-runtime-id <runtime-id> \
    --agent-runtime-artifact <artifact-config> \
    --role-arn <iam-role-arn> \
    --network-configuration <network-config> \
    [--description <text>] \
    [--authorizer-configuration <auth-config>] \
    [--request-header-configuration <header-config>] \
    [--protocol-configuration <protocol-config>] \
    [--lifecycle-configuration <lifecycle-config>] \
    [--environment-variables <env-vars>] \
    [--client-token <token>]
```

**Example:**

```bash
aws bedrock-agentcore-control update-agent-runtime \
    --agent-runtime-id abc123def456 \
    --agent-runtime-artifact '{
        "containerConfiguration": {
            "containerUri": "123456789012.dkr.ecr.ap-southeast-2.amazonaws.com/github-agent:v2.0.0"
        }
    }' \
    --role-arn arn:aws:iam::123456789012:role/AgentRuntimeRole \
    --network-configuration '{
        "networkMode": "VPC",
        "networkModeConfig": {
            "securityGroups": ["sg-0123456789abcdef0"],
            "subnets": ["subnet-0123456789abcdef0", "subnet-0123456789abcdef1"]
        }
    }' \
    --description "Updated GitHub agent with OAuth improvements" \
    --lifecycle-configuration '{
        "sessionTimeoutMinutes": 45,
        "maxLifetimeMinutes": 180
    }'
```

**Output:**

```json
{
  "agentRuntimeArn": "arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/github-agent",
  "agentRuntimeId": "abc123def456",
  "agentRuntimeVersion": "2",
  "status": "UPDATING"
}
```

---

### delete-agent-runtime

Deletes an agent runtime.

**Syntax:**

```bash
aws bedrock-agentcore-control delete-agent-runtime \
    --agent-runtime-id <runtime-id>
```

**Example:**

```bash
aws bedrock-agentcore-control delete-agent-runtime \
    --agent-runtime-id abc123def456
```

**Output:**

```json
{
  "agentRuntimeId": "abc123def456",
  "status": "DELETING"
}
```

---

## Gateway Management

### create-gateway

Creates an API gateway for agent access using Model Context Protocol (MCP).

**Syntax:**

```bash
aws bedrock-agentcore-control create-gateway \
    --name <gateway-name> \
    --role-arn <iam-role-arn> \
    --protocol-type <protocol> \
    --authorizer-type <auth-type> \
    [--description <text>] \
    [--protocol-configuration <config>] \
    [--authorizer-configuration <auth-config>] \
    [--kms-key-arn <kms-arn>] \
    [--exception-level <level>] \
    [--tags <tags>]
```

**Required Parameters:**

| Parameter           | Description                      | Values                    |
| ------------------- | -------------------------------- | ------------------------- |
| `--name`            | Unique gateway name              | 1-100 characters          |
| `--role-arn`        | IAM role for gateway permissions | ARN string                |
| `--protocol-type`   | Communication protocol           | Currently only `MCP`      |
| `--authorizer-type` | Authentication method            | `CUSTOM_JWT` or `AWS_IAM` |

**Example:**

```bash
aws bedrock-agentcore-control create-gateway \
    --name multi-agent-gateway \
    --role-arn arn:aws:iam::123456789012:role/AgentGatewayRole \
    --protocol-type MCP \
    --authorizer-type AWS_IAM \
    --description "Gateway for orchestrator and agent communication" \
    --exception-level DETAILED \
    --tags Key=Environment,Value=Production Key=Project,Value=MultiAgent
```

**Output:**

```json
{
  "gatewayArn": "arn:aws:bedrock:ap-southeast-2:123456789012:gateway/multi-agent-gateway",
  "gatewayId": "gw-abc123def456",
  "gatewayUrl": "https://abc123def456.execute-api.ap-southeast-2.amazonaws.com",
  "status": "CREATING"
}
```

---

### list-gateways

Lists all gateways in your account.

**Syntax:**

```bash
aws bedrock-agentcore-control list-gateways \
    [--starting-token <token>] \
    [--page-size <number>] \
    [--max-items <number>]
```

**Example:**

```bash
aws bedrock-agentcore-control list-gateways
```

---

### get-gateway

Retrieves detailed information about a specific gateway.

**Syntax:**

```bash
aws bedrock-agentcore-control get-gateway \
    --gateway-id <gateway-id>
```

**Example:**

```bash
aws bedrock-agentcore-control get-gateway \
    --gateway-id gw-abc123def456
```

---

### update-gateway

Updates gateway configuration.

**Syntax:**

```bash
aws bedrock-agentcore-control update-gateway \
    --gateway-id <gateway-id> \
    [--description <text>] \
    [--authorizer-configuration <auth-config>] \
    [--exception-level <level>]
```

**Example:**

```bash
aws bedrock-agentcore-control update-gateway \
    --gateway-id gw-abc123def456 \
    --description "Updated gateway with enhanced security" \
    --exception-level MINIMAL
```

---

### delete-gateway

Deletes a gateway.

**Syntax:**

```bash
aws bedrock-agentcore-control delete-gateway \
    --gateway-id <gateway-id>
```

**Example:**

```bash
aws bedrock-agentcore-control delete-gateway \
    --gateway-id gw-abc123def456
```

---

### Gateway Target Management

#### create-gateway-target

Associates an agent runtime with a gateway.

**Syntax:**

```bash
aws bedrock-agentcore-control create-gateway-target \
    --gateway-id <gateway-id> \
    --target-configuration <target-config>
```

**Example:**

```bash
aws bedrock-agentcore-control create-gateway-target \
    --gateway-id gw-abc123def456 \
    --target-configuration '{
        "agentRuntimeId": "abc123def456",
        "path": "/github-agent"
    }'
```

#### list-gateway-targets

Lists all targets associated with a gateway.

**Syntax:**

```bash
aws bedrock-agentcore-control list-gateway-targets \
    --gateway-id <gateway-id>
```

#### delete-gateway-target

Removes a target from a gateway.

**Syntax:**

```bash
aws bedrock-agentcore-control delete-gateway-target \
    --gateway-id <gateway-id> \
    --target-id <target-id>
```

#### sync-gateway-targets

Synchronizes gateway targets with latest configuration.

**Syntax:**

```bash
aws bedrock-agentcore-control sync-gateway-targets \
    --gateway-id <gateway-id>
```

---

## Credential Provider Management

### create-api-key-credential-provider

Creates an API key credential provider for agent authentication.

**Syntax:**

```bash
aws bedrock-agentcore-control create-api-key-credential-provider \
    --name <provider-name> \
    --api-key <api-key-value> \
    [--tags <tags>]
```

**Parameters:**

| Parameter   | Description          | Constraints                                        |
| ----------- | -------------------- | -------------------------------------------------- |
| `--name`    | Unique provider name | 1-128 characters, alphanumeric, hyphen, underscore |
| `--api-key` | API key value        | 1-65,536 characters                                |
| `--tags`    | Resource tags        | 0-50 tags                                          |

**Example:**

```bash
aws bedrock-agentcore-control create-api-key-credential-provider \
    --name github-api-credentials \
    --api-key "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
    --tags Key=Service,Value=GitHub Key=Environment,Value=Production
```

**Output:**

```json
{
  "credentialProviderArn": "arn:aws:bedrock:ap-southeast-2:123456789012:credential-provider/github-api-credentials",
  "name": "github-api-credentials",
  "apiKeySecretArn": "arn:aws:secretsmanager:ap-southeast-2:123456789012:secret:github-api-key-abc123"
}
```

---

### create-oauth2-credential-provider

Creates an OAuth2 credential provider for agent authentication.

**Syntax:**

```bash
aws bedrock-agentcore-control create-oauth2-credential-provider \
    --name <provider-name> \
    --oauth2-configuration <oauth2-config> \
    [--tags <tags>]
```

**Example:**

```bash
aws bedrock-agentcore-control create-oauth2-credential-provider \
    --name github-oauth-credentials \
    --oauth2-configuration '{
        "clientId": "Iv1.xxxxxxxxxxxx",
        "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "authorizationEndpoint": "https://github.com/login/oauth/authorize",
        "tokenEndpoint": "https://github.com/login/oauth/access_token",
        "scopes": ["repo", "user"]
    }' \
    --tags Key=Service,Value=GitHub Key=Type,Value=OAuth
```

---

### list-credential-providers

Lists all credential providers.

**Syntax:**

```bash
aws bedrock-agentcore-control list-credential-providers \
    [--credential-provider-type <type>] \
    [--starting-token <token>] \
    [--page-size <number>] \
    [--max-items <number>]
```

**Example:**

```bash
# List all credential providers
aws bedrock-agentcore-control list-credential-providers

# List only OAuth2 providers
aws bedrock-agentcore-control list-credential-providers \
    --credential-provider-type OAUTH2
```

---

### get-credential-provider

Retrieves credential provider details.

**Syntax:**

```bash
aws bedrock-agentcore-control get-credential-provider \
    --credential-provider-id <provider-id>
```

---

### delete-credential-provider

Deletes a credential provider.

**Syntax:**

```bash
aws bedrock-agentcore-control delete-credential-provider \
    --credential-provider-id <provider-id>
```

---

## Browser Management

### create-browser

Creates a browser instance for agent use.

**Syntax:**

```bash
aws bedrock-agentcore-control create-browser \
    --name <browser-name> \
    [--description <text>] \
    [--tags <tags>]
```

**Example:**

```bash
aws bedrock-agentcore-control create-browser \
    --name web-scraping-browser \
    --description "Browser instance for web automation tasks" \
    --tags Key=Purpose,Value=WebAutomation
```

---

### list-browsers

Lists all browser instances.

**Syntax:**

```bash
aws bedrock-agentcore-control list-browsers
```

---

### get-browser

Retrieves browser instance details.

**Syntax:**

```bash
aws bedrock-agentcore-control get-browser \
    --browser-id <browser-id>
```

---

### delete-browser

Deletes a browser instance.

**Syntax:**

```bash
aws bedrock-agentcore-control delete-browser \
    --browser-id <browser-id>
```

---

## Resource Tagging

### tag-resource

Adds or updates tags for a resource.

**Syntax:**

```bash
aws bedrock-agentcore-control tag-resource \
    --resource-arn <resource-arn> \
    --tags <key-value-pairs>
```

**Example:**

```bash
aws bedrock-agentcore-control tag-resource \
    --resource-arn arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/github-agent \
    --tags Key=Environment,Value=Production Key=CostCenter,Value=Engineering Key=Owner,Value=DevOps
```

---

### untag-resource

Removes tags from a resource.

**Syntax:**

```bash
aws bedrock-agentcore-control untag-resource \
    --resource-arn <resource-arn> \
    --tag-keys <key-list>
```

**Example:**

```bash
aws bedrock-agentcore-control untag-resource \
    --resource-arn arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/github-agent \
    --tag-keys Environment CostCenter
```

---

### list-tags-for-resource

Lists all tags associated with a resource.

**Syntax:**

```bash
aws bedrock-agentcore-control list-tags-for-resource \
    --resource-arn <resource-arn>
```

**Example:**

```bash
aws bedrock-agentcore-control list-tags-for-resource \
    --resource-arn arn:aws:bedrock:ap-southeast-2:123456789012:agent-runtime/github-agent
```

---

## Wait Commands

The `wait` command allows you to pause execution until a resource reaches a specific state.

### wait agent-runtime-ready

Waits until an agent runtime is in READY state.

**Syntax:**

```bash
aws bedrock-agentcore-control wait agent-runtime-ready \
    --agent-runtime-id <runtime-id>
```

**Example:**

```bash
aws bedrock-agentcore-control wait agent-runtime-ready \
    --agent-runtime-id abc123def456
```

---

### wait agent-runtime-deleted

Waits until an agent runtime is deleted.

**Syntax:**

```bash
aws bedrock-agentcore-control wait agent-runtime-deleted \
    --agent-runtime-id <runtime-id>
```

---

## Common Workflows

### 1. Complete Agent Deployment

```bash
# Step 1: Create agent runtime
aws bedrock-agentcore-control create-agent-runtime \
    --agent-runtime-name github-agent \
    --agent-runtime-artifact '{
        "containerConfiguration": {
            "containerUri": "123456789012.dkr.ecr.ap-southeast-2.amazonaws.com/github-agent:latest"
        }
    }' \
    --role-arn arn:aws:iam::123456789012:role/AgentRuntimeRole \
    --network-configuration '{
        "networkMode": "VPC",
        "networkModeConfig": {
            "securityGroups": ["sg-0123456789abcdef0"],
            "subnets": ["subnet-0123456789abcdef0"]
        }
    }' \
    --lifecycle-configuration '{
        "sessionTimeoutMinutes": 30,
        "maxLifetimeMinutes": 120
    }'

# Step 2: Wait for runtime to be ready
aws bedrock-agentcore-control wait agent-runtime-ready \
    --agent-runtime-id abc123def456

# Step 3: Create gateway
aws bedrock-agentcore-control create-gateway \
    --name multi-agent-gateway \
    --role-arn arn:aws:iam::123456789012:role/AgentGatewayRole \
    --protocol-type MCP \
    --authorizer-type AWS_IAM

# Step 4: Associate runtime with gateway
aws bedrock-agentcore-control create-gateway-target \
    --gateway-id gw-abc123def456 \
    --target-configuration '{
        "agentRuntimeId": "abc123def456",
        "path": "/github-agent"
    }'

# Step 5: Sync gateway targets
aws bedrock-agentcore-control sync-gateway-targets \
    --gateway-id gw-abc123def456
```

---

### 2. Update Agent to New Version

```bash
# Update agent runtime with new container image
aws bedrock-agentcore-control update-agent-runtime \
    --agent-runtime-id abc123def456 \
    --agent-runtime-artifact '{
        "containerConfiguration": {
            "containerUri": "123456789012.dkr.ecr.ap-southeast-2.amazonaws.com/github-agent:v2.0.0"
        }
    }' \
    --role-arn arn:aws:iam::123456789012:role/AgentRuntimeRole \
    --network-configuration '{
        "networkMode": "VPC",
        "networkModeConfig": {
            "securityGroups": ["sg-0123456789abcdef0"],
            "subnets": ["subnet-0123456789abcdef0"]
        }
    }' \
    --description "Updated to version 2.0.0 with OAuth improvements"

# Wait for update to complete
aws bedrock-agentcore-control wait agent-runtime-ready \
    --agent-runtime-id abc123def456

# Verify update
aws bedrock-agentcore-control get-agent-runtime \
    --agent-runtime-id abc123def456
```

---

### 3. Multi-Agent System Setup

```bash
# Create multiple agent runtimes
for agent in github-agent coding-agent planning-agent orchestrator-agent; do
    aws bedrock-agentcore-control create-agent-runtime \
        --agent-runtime-name $agent \
        --agent-runtime-artifact "{
            \"containerConfiguration\": {
                \"containerUri\": \"123456789012.dkr.ecr.ap-southeast-2.amazonaws.com/$agent:latest\"
            }
        }" \
        --role-arn arn:aws:iam::123456789012:role/AgentRuntimeRole \
        --network-configuration '{
            "networkMode": "VPC",
            "networkModeConfig": {
                "securityGroups": ["sg-0123456789abcdef0"],
                "subnets": ["subnet-0123456789abcdef0"]
            }
        }' \
        --tags Key=Project,Value=MultiAgent Key=Environment,Value=Production
done

# Create shared gateway
aws bedrock-agentcore-control create-gateway \
    --name multi-agent-shared-gateway \
    --role-arn arn:aws:iam::123456789012:role/AgentGatewayRole \
    --protocol-type MCP \
    --authorizer-type AWS_IAM

# Associate all agents with gateway
# (Retrieve runtime IDs first from list-agent-runtimes output)
aws bedrock-agentcore-control list-agent-runtimes --output json | \
    jq -r '.agentRuntimes[].agentRuntimeId' | \
    while read runtime_id; do
        aws bedrock-agentcore-control create-gateway-target \
            --gateway-id gw-abc123def456 \
            --target-configuration "{
                \"agentRuntimeId\": \"$runtime_id\",
                \"path\": \"/agent-$runtime_id\"
            }"
    done
```

---

### 4. OAuth Credential Setup for GitHub Agent

```bash
# Step 1: Create OAuth2 credential provider
aws bedrock-agentcore-control create-oauth2-credential-provider \
    --name github-oauth-prod \
    --oauth2-configuration '{
        "clientId": "Iv1.xxxxxxxxxxxx",
        "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "authorizationEndpoint": "https://github.com/login/oauth/authorize",
        "tokenEndpoint": "https://github.com/login/oauth/access_token",
        "scopes": ["repo", "user", "read:org"]
    }' \
    --tags Key=Service,Value=GitHub Key=Environment,Value=Production

# Step 2: Update agent runtime with credential provider
# (Note: This would be configured in the agent's code to use the credential provider)

# Step 3: Verify credential provider
aws bedrock-agentcore-control get-credential-provider \
    --credential-provider-id cp-abc123def456
```

---

## Best Practices

### 1. Resource Naming Conventions

- **Agent Runtimes**: Use descriptive names like `{service}-agent` (e.g., `github-agent`, `jira-agent`)
- **Gateways**: Use purpose-based names like `{project}-{environment}-gateway`
- **Credential Providers**: Use service and type in name like `{service}-{type}-{environment}`

### 2. Network Configuration

**VPC Mode (Recommended for Production)**:

```json
{
  "networkMode": "VPC",
  "networkModeConfig": {
    "securityGroups": ["sg-xxxxx"],
    "subnets": ["subnet-xxxxx", "subnet-yyyyy"]
  }
}
```

**Public Mode (Development/Testing Only)**:

```json
{
  "networkMode": "PUBLIC"
}
```

### 3. Lifecycle Configuration

Set appropriate timeouts based on agent workload:

- **Short tasks** (< 5 min): `sessionTimeoutMinutes: 10`
- **Medium tasks** (5-30 min): `sessionTimeoutMinutes: 30`
- **Long tasks** (> 30 min): `sessionTimeoutMinutes: 60`

Always set `maxLifetimeMinutes` to prevent runaway sessions.

### 4. Environment Variables

Organize environment variables by category:

```json
{
  "AWS_REGION": "ap-southeast-2",
  "LOG_LEVEL": "INFO",
  "MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
  "GITHUB_API_VERSION": "2022-11-28",
  "MAX_RETRIES": "3"
}
```

### 5. Tagging Strategy

Use consistent tags across all resources:

```bash
--tags \
    Key=Project,Value=MultiAgent \
    Key=Environment,Value=Production \
    Key=Owner,Value=DevOps \
    Key=CostCenter,Value=Engineering \
    Key=ManagedBy,Value=Terraform
```

### 6. Security

- **IAM Roles**: Use least-privilege principle
- **Credential Providers**: Rotate credentials regularly
- **Network Security**: Use VPC mode with restrictive security groups
- **KMS Encryption**: Use customer-managed keys for sensitive data
- **Authorization**: Prefer AWS_IAM over CUSTOM_JWT when possible

### 7. Monitoring and Logging

```bash
# Tag resources for cost tracking
aws bedrock-agentcore-control tag-resource \
    --resource-arn <arn> \
    --tags Key=CostCenter,Value=Engineering

# Use CloudWatch Logs for runtime logs
# Configure log retention in lifecycle settings

# Monitor runtime status
aws bedrock-agentcore-control get-agent-runtime \
    --agent-runtime-id <id> \
    --query 'status'
```

### 8. Update Strategy

**Blue-Green Deployment**:

1. Create new runtime version with updated container
2. Test new version
3. Update gateway targets to point to new version
4. Monitor for issues
5. Delete old version after successful deployment

**Rolling Update**:

1. Update runtime with new configuration
2. Wait for READY status
3. Gradually shift traffic using gateway targets
4. Monitor metrics and rollback if needed

---

## Troubleshooting

### Common Issues

#### 1. Runtime Creation Fails

**Problem**: Agent runtime stuck in CREATING or transitions to FAILED

**Solutions**:

- Check IAM role permissions
- Verify ECR repository access
- Ensure VPC configuration is correct (subnets, security groups)
- Check CloudWatch Logs for container startup errors

```bash
# Check runtime status
aws bedrock-agentcore-control get-agent-runtime \
    --agent-runtime-id <id> \
    --query '[status, statusReason]'

# View CloudWatch logs
aws logs tail /aws/bedrock-agentcore/<runtime-name> --follow
```

---

#### 2. Gateway Target Association Fails

**Problem**: Cannot associate agent runtime with gateway

**Solutions**:

- Ensure runtime is in READY state
- Verify gateway role has invoke permissions
- Check network connectivity between gateway and runtime
- Sync gateway targets after changes

```bash
# Verify runtime is ready
aws bedrock-agentcore-control get-agent-runtime \
    --agent-runtime-id <id> \
    --query 'status'

# Sync targets
aws bedrock-agentcore-control sync-gateway-targets \
    --gateway-id <gateway-id>
```

---

#### 3. Authentication Errors

**Problem**: Agent cannot authenticate with external services

**Solutions**:

- Verify credential provider configuration
- Check OAuth scopes match requirements
- Rotate expired credentials
- Test credentials independently

```bash
# Get credential provider details
aws bedrock-agentcore-control get-credential-provider \
    --credential-provider-id <id>

# Recreate credential provider if needed
aws bedrock-agentcore-control delete-credential-provider \
    --credential-provider-id <id>

aws bedrock-agentcore-control create-oauth2-credential-provider \
    --name <name> \
    --oauth2-configuration <config>
```

---

#### 4. Performance Issues

**Problem**: Slow response times or timeouts

**Solutions**:

- Increase `sessionTimeoutMinutes` in lifecycle configuration
- Optimize container image size
- Use VPC endpoints for AWS service access
- Monitor CloudWatch metrics

```bash
# Update lifecycle configuration
aws bedrock-agentcore-control update-agent-runtime \
    --agent-runtime-id <id> \
    --lifecycle-configuration '{
        "sessionTimeoutMinutes": 60,
        "maxLifetimeMinutes": 180
    }'
```

---

#### 5. Resource Quotas Exceeded

**Problem**: Cannot create new resources due to service limits

**Solutions**:

- Request service limit increase via AWS Support
- Delete unused runtimes and gateways
- Use shared gateways for multiple agents
- Consolidate resources across regions

```bash
# List all resources to identify unused ones
aws bedrock-agentcore-control list-agent-runtimes
aws bedrock-agentcore-control list-gateways
aws bedrock-agentcore-control list-browsers

# Delete unused resources
aws bedrock-agentcore-control delete-agent-runtime \
    --agent-runtime-id <id>
```

---

## Cost Optimization

### 1. Resource Cleanup

Regularly identify and delete unused resources:

```bash
# List runtimes not updated in 30 days
aws bedrock-agentcore-control list-agent-runtimes --output json | \
    jq -r '.agentRuntimes[] |
        select((.lastUpdatedAt | fromdateiso8601) < (now - 2592000)) |
        .agentRuntimeId'

# Delete old runtimes
# (Review output first, then delete)
```

### 2. Lifecycle Management

Configure appropriate timeouts to prevent unnecessary charges:

- Set `sessionTimeoutMinutes` based on actual usage
- Use `maxLifetimeMinutes` to prevent runaway sessions
- Monitor session duration in CloudWatch

### 3. Shared Resources

- Use one gateway for multiple agents
- Share VPC resources across runtimes
- Consolidate credential providers

### 4. Right-Sizing

- Use smaller container images
- Optimize agent code for efficiency
- Monitor memory and CPU usage

---

## Related Documentation

- [AWS Bedrock AgentCore User Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [AWS CLI Command Reference](https://docs.aws.amazon.com/cli/latest/reference/bedrock-agentcore-control/)
- [AgentCore Runtime Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-runtime.html)
- [Bedrock Agent Runtime API](https://docs.aws.amazon.com/cli/latest/reference/bedrock-agent-runtime/)
- [IAM Permissions for AgentCore](https://docs.aws.amazon.com/bedrock/latest/userguide/security-iam.html)

---

## Quick Reference

### Essential Commands

```bash
# List all resources
aws bedrock-agentcore-control list-agent-runtimes
aws bedrock-agentcore-control list-gateways
aws bedrock-agentcore-control list-credential-providers

# Get resource details
aws bedrock-agentcore-control get-agent-runtime --agent-runtime-id <id>
aws bedrock-agentcore-control get-gateway --gateway-id <id>

# Create agent runtime
aws bedrock-agentcore-control create-agent-runtime \
    --agent-runtime-name <name> \
    --agent-runtime-artifact <artifact> \
    --role-arn <role> \
    --network-configuration <config>

# Update agent runtime
aws bedrock-agentcore-control update-agent-runtime \
    --agent-runtime-id <id> \
    --agent-runtime-artifact <artifact> \
    --role-arn <role> \
    --network-configuration <config>

# Delete agent runtime
aws bedrock-agentcore-control delete-agent-runtime \
    --agent-runtime-id <id>

# Wait for ready
aws bedrock-agentcore-control wait agent-runtime-ready \
    --agent-runtime-id <id>

# Tag resources
aws bedrock-agentcore-control tag-resource \
    --resource-arn <arn> \
    --tags Key=Name,Value=Value
```

### Status Values

**Agent Runtime Status**:

- `CREATING` - Runtime is being created
- `READY` - Runtime is ready for use
- `UPDATING` - Runtime is being updated
- `DELETING` - Runtime is being deleted
- `FAILED` - Runtime creation/update failed

**Gateway Status**:

- `CREATING` - Gateway is being created
- `READY` - Gateway is ready
- `UPDATING` - Gateway is being updated
- `DELETING` - Gateway is being deleted
- `FAILED` - Gateway operation failed

---

## Support and Feedback

For issues, questions, or feedback:

- AWS Support Console: https://console.aws.amazon.com/support/
- AWS Documentation: https://docs.aws.amazon.com/bedrock/
- AWS Forums: https://repost.aws/

**Note**: Amazon Bedrock AgentCore Control is in preview and subject to change. Always refer to the latest AWS documentation for the most current information.
