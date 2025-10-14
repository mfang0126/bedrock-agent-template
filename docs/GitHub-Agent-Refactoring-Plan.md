# GitHub Agent Refactoring Plan

**Goal**: Separate local-testable agent logic from AgentCore deployment wrapper to enable fast local development.

**Status**: Planning  
**Priority**: High  
**Estimated Time**: 4-6 hours

---

## Overview

### Current Structure (Problematic)
```
agents/github-agent/src/
├── runtime.py          # Mixed: AgentCore + Agent logic
├── common/
│   ├── auth.py         # AgentCore-only (@requires_access_token)
│   ├── config.py
│   └── utils.py
└── tools/              # Depends on global auth state
    ├── repos.py
    ├── issues.py
    └── pull_requests.py
```

**Problem**: Cannot test without deploying to AgentCore. OAuth decorator and global state block local execution.

### Target Structure (Testable)
```
agents/github-agent/
├── src/
│   ├── agent.py                    # NEW: Pure agent logic
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── interface.py            # NEW: Auth interface
│   │   ├── mock.py                 # NEW: Mock for local
│   │   └── agentcore.py            # MOVED: Real OAuth
│   ├── tools/
│   │   ├── repos.py                # REFACTOR: Use auth interface
│   │   ├── issues.py               # REFACTOR: Use auth interface
│   │   └── pull_requests.py       # REFACTOR: Use auth interface
│   ├── common/
│   │   ├── config.py
│   │   └── utils.py
│   └── runtime.py                  # REFACTOR: Thin wrapper only
├── test_local.py                   # NEW: Local test script
└── tests/                          # NEW: Unit tests
    ├── test_tools.py
    └── test_agent.py
```

**Benefits**: Test 90% of logic locally in seconds. Deploy only validates OAuth and real APIs.

---

## Phase 1: Create Auth Abstraction

### 1.1 Create Auth Interface

- [ ] Create `src/auth/` directory
- [ ] Create `src/auth/interface.py`
  - Define abstract `GitHubAuth` class
  - Single method: `async def get_token() -> str`
  - Add docstring explaining purpose

### 1.2 Create Mock Implementation

- [ ] Create `src/auth/mock.py`
  - Implement `MockGitHubAuth(GitHubAuth)`
  - Return hardcoded token: `ghp_mock_token_for_testing`
  - Add logging to show it's mock mode

### 1.3 Move Real OAuth to Separate Module

- [ ] Create `src/auth/agentcore.py`
- [ ] Copy OAuth logic from `src/common/auth.py`:
  - `@requires_access_token` decorator
  - `on_auth_url` callback
  - Token storage logic
- [ ] Wrap in `AgentCoreGitHubAuth(GitHubAuth)` class
- [ ] Keep existing OAuth URL streaming logic intact
- [ ] Add logging to show it's AgentCore mode

### 1.4 Create Auth Factory

- [ ] Create `src/auth/__init__.py`
- [ ] Add factory function: `get_auth_provider(env: str) -> GitHubAuth`
  - If `env == "local"` → return `MockGitHubAuth()`
  - Else → return `AgentCoreGitHubAuth()`

**Validation**: Can import and instantiate both auth classes without errors.

---

## Phase 2: Refactor Tools

### 2.1 Update Repos Tools

- [ ] Edit `src/tools/repos.py`
- [ ] Remove dependency on `src.common.auth`
- [ ] Add `GitHubRepoTools` class:
  - Constructor accepts `auth: GitHubAuth`
  - All tool methods become instance methods
  - Replace `get_cached_token()` with `await self.auth.get_token()`
- [ ] Keep all existing tool logic unchanged
- [ ] Update docstrings

**Tools to update**:
- [ ] `list_github_repos`
- [ ] `get_repo_info`
- [ ] `create_github_repo`

### 2.2 Update Issues Tools

- [ ] Edit `src/tools/issues.py`
- [ ] Add `GitHubIssueTools` class
- [ ] Same pattern as repos tools

**Tools to update**:
- [ ] `list_github_issues`
- [ ] `create_github_issue`
- [ ] `close_github_issue`
- [ ] `update_github_issue`
- [ ] `post_github_comment`

### 2.3 Update Pull Request Tools

- [ ] Edit `src/tools/pull_requests.py`
- [ ] Add `GitHubPRTools` class
- [ ] Same pattern as repos tools

**Tools to update**:
- [ ] `list_pull_requests`
- [ ] `create_pull_request`
- [ ] `merge_pull_request`

**Validation**: Tools can be instantiated with mock auth and methods are callable.

---

## Phase 3: Extract Agent Logic

### 3.1 Create Pure Agent Module

- [ ] Create `src/agent.py`
- [ ] Define `create_github_agent(auth: GitHubAuth) -> Agent` function
- [ ] Instantiate all tool classes:
  - `repo_tools = GitHubRepoTools(auth)`
  - `issue_tools = GitHubIssueTools(auth)`
  - `pr_tools = GitHubPRTools(auth)`
- [ ] Create Strands Agent with all tool methods
- [ ] Copy system prompt from current `runtime.py`
- [ ] Add model configuration (Claude 3.5 Sonnet)

### 3.2 Add Configuration

- [ ] Update `src/common/config.py`
- [ ] Add environment detection:
  - `get_environment() -> str` (returns "local", "dev", or "prod")
  - Read from `AGENT_ENV` environment variable
- [ ] Add model configuration:
  - Model ID
  - Region
  - Temperature settings

**Validation**: Can call `create_github_agent(MockGitHubAuth())` successfully.

---

## Phase 4: Create Local Testing

### 4.1 Create Test Script

- [ ] Create `test_local.py` in agent root
- [ ] Import `create_github_agent` and `MockGitHubAuth`
- [ ] Add main block:
  - Set up logging (DEBUG level)
  - Create agent with mock auth
  - Test basic queries:
    - "List my repos"
    - "What repos do I have?"
    - "Create a test issue"
  - Print results

### 4.2 Add Unit Tests

- [ ] Create `tests/` directory
- [ ] Create `tests/test_tools.py`:
  - Test tool parameter validation
  - Test error handling
  - Mock HTTP responses
- [ ] Create `tests/test_agent.py`:
  - Test agent creation
  - Test tool selection
  - Test response formatting

**Validation**: `python test_local.py` runs successfully and shows mock responses.

---

## Phase 5: Refactor Runtime

### 5.1 Simplify Runtime Entrypoint

- [ ] Edit `src/runtime.py`
- [ ] Remove all agent logic (tools, model config)
- [ ] Import `create_github_agent` from `agent.py`
- [ ] Import `get_auth_provider` from `auth`
- [ ] Update `@app.entrypoint` to:
  - Detect environment
  - Get appropriate auth provider
  - Create agent using `create_github_agent(auth)`
  - Stream responses

### 5.2 Preserve OAuth Streaming

- [ ] Keep OAuth URL callback mechanism
- [ ] Keep streaming logic for OAuth URLs
- [ ] Ensure `oauth_url_queue` still works
- [ ] Keep all error handling

### 5.3 Clean Up Old Files

- [ ] Delete or archive `src/common/auth.py` (moved to `auth/agentcore.py`)
- [ ] Review `src/common/utils.py` - keep shared utilities
- [ ] Update imports across all files

**Validation**: `agentcore launch --local` still works.

---

## Phase 6: Environment Configuration

### 6.1 Create Environment Files

- [ ] Create `.env.local`:
  - `AGENT_ENV=local`
  - `LOG_LEVEL=DEBUG`
- [ ] Create `.env.dev`:
  - `AGENT_ENV=dev`
  - `GITHUB_CLIENT_ID=<dev-id>`
  - `LOG_LEVEL=INFO`
- [ ] Update `.env.example` with all variables

### 6.2 Update .gitignore

- [ ] Ensure `.env.local` is ignored
- [ ] Ensure `.env.dev` is ignored
- [ ] Keep `.env.example` tracked

**Validation**: Can switch environments via `AGENT_ENV` variable.

---

## Phase 7: Testing & Validation

### 7.1 Local Testing

- [ ] Run `python test_local.py`
- [ ] Test all tool categories:
  - Repository operations
  - Issue operations
  - Pull request operations
- [ ] Verify mock responses
- [ ] Check logging output
- [ ] Test error scenarios

### 7.2 Local AgentCore Testing

- [ ] Set `AGENT_ENV=local`
- [ ] Run `agentcore launch --local`
- [ ] Run `agentcore invoke --message "List repos"`
- [ ] Verify mock auth is used
- [ ] Check Docker logs

### 7.3 Dev Deployment Testing

- [ ] Set `AGENT_ENV=dev`
- [ ] Deploy: `agentcore deploy --agent github-dev`
- [ ] Test OAuth flow:
  - Invoke without prior auth
  - Verify OAuth URL generation
  - Complete OAuth flow
- [ ] Test real GitHub operations:
  - List actual repositories
  - Create test issue
  - List pull requests
- [ ] Verify AgentCore Memory works
- [ ] Check CloudWatch logs

### 7.4 Prod Deployment Testing

- [ ] Set `AGENT_ENV=prod`
- [ ] Deploy: `agentcore deploy --agent github-prod`
- [ ] Run smoke tests only:
  - Basic OAuth flow
  - One repo list operation
- [ ] Verify observability
- [ ] Set up CloudWatch alarms

---

## Phase 8: Documentation

### 8.1 Update README

- [ ] Add local development section
- [ ] Document `test_local.py` usage
- [ ] Add environment setup instructions
- [ ] Update deployment instructions

### 8.2 Create Developer Guide

- [ ] Create `docs/GitHub-Agent-Development-Guide.md`:
  - Local development workflow
  - Testing strategy
  - Debugging tips
  - Common issues

### 8.3 Update Migration Guide

- [ ] Update `MIGRATION_GUIDE.md`
- [ ] Add GitHub agent as reference implementation
- [ ] Document new architecture pattern

---

## Success Criteria

- [ ] ✅ Can run `python test_local.py` without AWS/AgentCore
- [ ] ✅ Can test tool logic in < 5 seconds
- [ ] ✅ Can debug with Python debugger (breakpoints work)
- [ ] ✅ OAuth flow still works in dev/prod
- [ ] ✅ Real GitHub API integration works in dev/prod
- [ ] ✅ AgentCore Memory persists across sessions
- [ ] ✅ No regression in existing functionality
- [ ] ✅ Code is cleaner and more maintainable

---

## Rollback Plan

If issues arise during refactoring:

1. Git branch created before changes: `git checkout main`
2. Tagged stable version: `git tag v1.0-pre-refactor`
3. Keep old `auth.py` as `auth.py.backup` until validation complete
4. Test in dev environment before touching prod

---

## Timeline

- **Phase 1**: 1 hour (Auth abstraction)
- **Phase 2**: 1.5 hours (Refactor tools)
- **Phase 3**: 30 minutes (Extract agent)
- **Phase 4**: 30 minutes (Local testing)
- **Phase 5**: 1 hour (Refactor runtime)
- **Phase 6**: 30 minutes (Environment config)
- **Phase 7**: 1.5 hours (Testing & validation)
- **Phase 8**: 30 minutes (Documentation)

**Total**: 6-7 hours

---

## Next Steps

After GitHub agent refactoring is complete:

1. Apply same pattern to Planning Agent (simpler - no OAuth)
2. Apply to JIRA Agent (similar OAuth pattern)
3. Apply to Coding Agent (no OAuth)
4. Build Orchestrator Agent using Agents-as-Tools pattern

---

## Notes

- **No breaking changes** to deployed agents during refactoring
- Test in dev environment before prod
- Keep existing OAuth streaming behavior intact
- Maintain backward compatibility with current `.bedrock_agentcore.yaml`
- All existing functionality must work exactly the same after refactoring
