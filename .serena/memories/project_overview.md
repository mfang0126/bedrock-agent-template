# Multi-Agent Platform - Project Overview

## Purpose
Production-ready multi-agent platform template using AWS Bedrock AgentCore with OAuth 2.0 (3-Legged OAuth) integration. Demonstrates secure per-user token management for GitHub API operations.

**Key Innovation**: User-isolated OAuth tokens - each user gets their own secure GitHub access token managed by AgentCore Identity.

## Current State
✅ **GitHub Agent**: Production-ready with OAuth 3LO device flow
🚧 **Template Status**: Ready for extending to other OAuth providers (Jira, Slack, etc.)

## Architecture Components
1. **AgentCore Runtime**: Serverless agent execution with Claude 3.7 Sonnet
2. **AgentCore Identity**: User-specific OAuth token management (encrypted per-user)
3. **Strands Framework**: Agent orchestration with tool coordination
4. **GitHub OAuth**: Device Flow (3LO) for user authorization
5. **Real API Integration**: httpx-based GitHub API calls with user tokens

## Key Features
- **Multi-tenant**: Per-user OAuth token isolation
- **Secure**: AgentCore Identity manages encrypted tokens
- **Scalable**: Serverless architecture, pay-per-use
- **Production-ready**: Follows AWS notebook patterns
- **Extensible**: Template for adding more OAuth providers

## Tech Stack
- **Language**: Python 3.10+
- **Package Manager**: uv
- **Agent Framework**: Strands (bedrock-agentcore[strands-agents])
- **Model**: Claude 3.7 Sonnet (us.anthropic.claude-3-7-sonnet-20250219-v1:0)
- **HTTP Client**: httpx
- **CLI**: typer
- **AWS SDK**: boto3
- **Config**: python-dotenv

## Current Capabilities
**Repository Tools**:
- list_github_repos: List user's repositories with stats
- get_repo_info: Get detailed repository information
- create_github_repo: Create new repositories

**Issue Tools**:
- list_github_issues: List issues in a repository
- create_github_issue: Create new issues
- close_github_issue: Close existing issues
