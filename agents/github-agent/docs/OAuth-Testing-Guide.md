# OAuth Testing Guide for GitHub Agent

## Overview

The GitHub Agent uses **OAuth 3LO (Three-Legged OAuth)** for user authentication, which requires the `--user-id` flag when invoking the agent.

## Why `--user-id` is Required

AgentCore implements **User Federation** OAuth, which means:

- Each user gets their own separate GitHub token
- Tokens are scoped to individual users
- AgentCore needs to know which user is making the request
- The `--user-id` flag provides this user context

Without `--user-id`, AgentCore cannot:
- Associate the OAuth flow with a specific user
- Store or retrieve user-specific tokens
- Complete the authentication process

## Correct Usage

### Basic Invocation
```bash
agentcore invoke --user-id YOUR_USERNAME --message "List my repositories"
```

### With Agent Name
```bash
agentcore invoke --agent github-dev --user-id YOUR_USERNAME --message "List my repositories"
```

### Local Testing with OAuth
```bash
# Terminal 1: Launch agent
export AGENT_ENV=dev
agentcore launch --local

# Terminal 2: Invoke with user ID
agentcore invoke --user-id mingfang --message "List my repositories"
```

## What to Use as `--user-id`

The `--user-id` can be **any identifier** that you consistently use for your testing. Common choices:

✅ **Recommended Options:**
- Your GitHub username: `--user-id mingfang`
- Your email: `--user-id user@example.com`
- A test identifier: `--user-id test-user-1`

❌ **Not Required:**
- Real user ID from database
- UUID or special format
- Pre-registered user

**The key is consistency** - use the same ID across sessions to reuse cached tokens.

## OAuth Flow with `--user-id`

### First Invocation (No Token Yet)
```bash
agentcore invoke --user-id mingfang --message "List my repositories"
```

**What Happens:**
1. Agent checks for cached token for user `mingfang`
2. No token found → Triggers OAuth flow
3. Agent returns OAuth URL:
   ```
   🔗 Please authorize at: https://github.com/login/oauth/authorize?...
   ```
4. You visit URL in browser and authorize
5. Token is cached for user `mingfang`

### Subsequent Invocations (Token Cached)
```bash
agentcore invoke --user-id mingfang --message "Create an issue"
```

**What Happens:**
1. Agent finds cached token for user `mingfang`
2. Uses token directly (no OAuth flow)
3. Makes real GitHub API call
4. Returns result

## Environment-Specific Behavior

### `AGENT_ENV=local` (Mock Mode)
```bash
export AGENT_ENV=local
agentcore invoke --user-id mingfang --message "test"
```

- Uses `MockGitHubAuth` (fake token)
- No real OAuth flow
- `--user-id` not strictly required but good practice

### `AGENT_ENV=dev` or `AGENT_ENV=prod` (Real OAuth)
```bash
export AGENT_ENV=dev
agentcore invoke --user-id mingfang --message "test"
```

- Uses `AgentCoreGitHubAuth` (real OAuth)
- **`--user-id` is REQUIRED**
- Triggers OAuth flow on first use

## Common Errors

### Error: "GitHub authentication required"
**Cause:** Missing or incorrect OAuth flow

**Solution:**
```bash
# Ensure you're using --user-id
agentcore invoke --user-id YOUR_USERNAME --message "test"
```

### Error: Token expired
**Cause:** Cached token expired

**Solution:**
```bash
# Force re-authentication by using different user-id or clearing cache
agentcore invoke --user-id YOUR_USERNAME --message "test"
# Follow new OAuth URL
```

## Testing Checklist

- [ ] Set `AGENT_ENV=dev` for real OAuth
- [ ] Launch agent: `agentcore launch --local`
- [ ] Invoke with `--user-id`: `agentcore invoke --user-id YOUR_USERNAME --message "test"`
- [ ] Complete OAuth flow in browser
- [ ] Verify token is cached (subsequent calls skip OAuth)
- [ ] Test real GitHub API operations

## Architecture Notes

### How `--user-id` Works Internally

1. **Request Reception:**
   ```python
   # AgentCore runtime receives user_id from CLI
   user_id = payload.get("user_id")
   ```

2. **Token Lookup:**
   ```python
   # @requires_access_token decorator uses user_id for token storage
   @requires_access_token(
       provider_name="github-provider",
       auth_flow="USER_FEDERATION",  # Uses user context
       ...
   )
   ```

3. **Token Storage:**
   - Tokens stored per user in AgentCore's credential store
   - Key format: `{provider_name}:{user_id}`
   - Example: `github-provider:mingfang`

### Why User Federation?

User Federation (3LO) is required for:
- ✅ Acting on behalf of the authenticated user
- ✅ User-specific permissions and access
- ✅ Proper audit trails
- ✅ Token isolation between users

## Quick Reference

| Scenario | Command |
|----------|---------|
| First time (OAuth) | `agentcore invoke --user-id USER --message "test"` |
| Subsequent calls | `agentcore invoke --user-id USER --message "test"` |
| Local mock mode | `AGENT_ENV=local agentcore invoke --message "test"` |
| Production | `agentcore invoke --agent github-prod --user-id USER --message "test"` |

## Summary

✅ **Always use `--user-id` when testing OAuth**
✅ **Use consistent user ID to reuse tokens**
✅ **First call triggers OAuth, subsequent calls reuse token**
✅ **User ID can be any identifier (username, email, etc.)**

---

For more testing scenarios, see:
- **TESTING_GUIDE.md** - Complete testing documentation
- **README_TESTING.md** - Quick testing reference
- **QUICKSTART.md** - Getting started guide
