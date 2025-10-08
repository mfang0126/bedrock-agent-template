# Git Agent Implementation Plan

**Status Legend:**
- ⬜ Not Started
- 🟡 In Progress
- ✅ Completed
- ❌ Blocked

**Last Updated:** 2024 (Updated with current project status)

**Project Location:** `/Users/ming.fang/Code/ai-coding-agents/app`

---

## 📊 Implementation Progress

**Overall Status:** 🟡 40% Complete

| Phase | Status | Progress | Remaining Work |
|-------|--------|----------|----------------|
| Phase 1: Core Infrastructure | ✅ | 100% | None |
| Phase 2: Issue Management | 🟡 | 70% | Add comment tool |
| Phase 3: Repository Operations | 🟡 | 40% | Git ops (clone, branch, commit) |
| Phase 4: Pull Request Management | ⬜ | 0% | All PR tools |
| Phase 5: Integration & Error Handling | ⬜ | 0% | Utilities |
| Phase 6: Testing & Deployment | 🟡 | 30% | Tests needed |
| Phase 7: Documentation | 🟡 | 50% | API docs |

---

## 🎯 Quick Reference

**What's Already Working:**
```bash
# Authenticate first
authenticate --to=wealth-dev-au

# Invoke the deployed agent
agentcore invoke '{"prompt": "list my repositories"}' --user-id "user-123"
agentcore invoke '{"prompt": "create an issue in myrepo"}' --user-id "user-123"
```

**Available Tools (6):**
1. list_github_repos - List user's repositories
2. get_repo_info - Get detailed repo information
3. create_github_repo - Create new repository
4. list_github_issues - List issues in a repo
5. create_github_issue - Create new issue
6. close_github_issue - Close an issue

**What's Missing:**
- Post comments on issues
- Git operations (clone, branch, commit, push)
- Pull request management

**Simplified Approach:**
- ❌ No CLI interface
- ❌ No unit tests with mocks
- ✅ Only real integration tests
- ✅ Focus on core features

---

## Overview

The Git Agent is responsible for all GitHub operations including repository management, issue tracking, pull requests, and code synchronization. It acts as the bridge between the orchestrator and GitHub's API/Git operations.

---

## Phase 1: Core Infrastructure ✅

### 1.1 Authentication Setup ✅

**Status:** Already implemented in `src/common/auth/github.py`

**Implementation Details:**
- ✅ GitHub OAuth 2.0 Device Flow (3LO pattern) implemented
- ✅ AgentCore Identity integration with @requires_access_token
- ✅ Per-user token isolation for multi-tenant security
- ✅ OAuth provider setup script: `setup_github_provider.py`

**Existing Files:**
- `src/common/auth/github.py` - OAuth decorator and token management
- `src/common/config/config.py` - Configuration management
- `setup_github_provider.py` - Provider setup script
- `.env` - Credentials (GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET)

**Required Scopes (Already Configured):**
- `repo` (full repository access)
- `read:user` (user profile)

**Core Logic:**
```
FUNCTION authenticate_user(user_id):
    IF token_exists_in_agentcore(user_id):
        RETURN retrieve_token(user_id)
    ELSE:
        TRIGGER device_flow_oauth()
        WAIT for user_authorization
        STORE token_in_agentcore(user_id, token)
        RETURN token
```

---

### 1.2 Base Agent Structure ✅

**Status:** Already implemented in `src/agents/github_agent/`

**Implementation Details:**
- ✅ BedrockAgentCoreApp entrypoint created
- ✅ Agent with Claude 3.5 Sonnet model configured
- ✅ Tools registered with the agent
- ✅ Standardized request/response protocol

**Existing Files:**
- `src/agents/github_agent/runtime.py` - AgentCore entrypoint (DEPLOYED)
- `src/agents/github_agent/agent.py` - Agent logic
- `src/agents/github_agent/__main__.py` - CLI interface

**Current Model:** `anthropic.claude-3-5-sonnet-20241022-v2:0` (ap-southeast-2 region)

**System Prompt (Current):**
```
You are a helpful GitHub assistant that helps users manage their GitHub repositories and issues.

You have access to tools for:
- Listing repositories
- Getting repository information
- Creating repositories
- Listing issues
- Creating issues
- Closing issues

When users ask about their GitHub account, use the appropriate tools to help them.
Provide clear, friendly responses with relevant information formatted nicely.
```

**Core Logic:**
```
CLASS GitAgent:
    PROPERTIES:
        - model: Claude 3.5 Sonnet
        - tools: [list_repos, create_issue, post_comment, ...]
        - auth_provider: GitHubOAuthProvider
        - http_client: httpx.AsyncClient
    
    METHOD handle_request(payload, user_id):
        action = payload.get("action")
        AUTHENTICATE user_id
        ROUTE to appropriate tool based on action
        EXECUTE tool with payload
        RETURN standardized response
```

---

## Phase 2: Issue Management Tools 🟡 (70% Complete)

**Completed:**
- ✅ list_github_issues
- ✅ create_github_issue
- ✅ close_github_issue

**Remaining:**
- ⬜ post_github_comment (add to issues.py)
- ⬜ update_github_issue (full update capability) 🟡

### 2.1 Create Issue Tool ⬜

**Implementation Details:**
- POST to `/repos/{owner}/{repo}/issues`
- Support markdown formatting in body
- Handle labels, assignees, milestones
- Return issue URL and number

**Core Logic:**
```
FUNCTION create_issue(title, body, repo, labels=[], assignees=[]):
    VALIDATE inputs (title not empty, repo format correct)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json"
    }
    
    payload = {
        "title": title,
        "body": body,
        "labels": labels,
        "assignees": assignees
    }
    
    response = httpx.post(
        f"https://api.github.com/repos/{repo}/issues",
        headers=headers,
        json=payload
    )
    
    IF response.status_code == 201:
        issue_data = response.json()
        RETURN {
            "status": "success",
            "result": {
                "issue_url": issue_data["html_url"],
                "issue_number": issue_data["number"],
                "created_at": issue_data["created_at"]
            }
        }
    ELSE:
        RETURN error_response(response)
```

**Files to Create:**
- `src/tools/github/issues.py`

**Tool Decorator:**
```python
@tool
@requires_access_token(provider_name="github-provider")
def create_github_issue(title: str, body: str, repo: str, labels: list = None, assignees: list = None) -> str
```

---

### 2.2 List Issues Tool ✅

**Status:** Already implemented in `src/tools/github/issues.py`

**Implementation Details:**
- ✅ GET from `/repos/{owner}/{repo}/issues`
- ✅ Supports filtering by state (open, closed, all)
- ✅ Returns formatted issue list with labels, author, dates
- ✅ Emoji formatting for better readability

**Existing Implementation:**
```python
@tool
def list_github_issues(repo_name: str, state: str = "open") -> str
```

**Core Logic:** (Already implemented)
```
FUNCTION list_issues(repo, state="open"):
    response = httpx.get(f"https://api.github.com/repos/{repo}/issues", params={"state": state})
    FORMAT issues with emoji, labels, dates, author
    RETURN formatted string
```

---

### 2.3 Post Comment Tool ⬜

**Status:** NOT YET IMPLEMENTED - Need to add

**Implementation Details:**
- POST to `/repos/{owner}/{repo}/issues/{issue_number}/comments`
- Support markdown formatting
- Handle mentions (@username)
- Return comment ID and URL

**Core Logic:**
```
FUNCTION post_comment(repo, issue_number, comment):
    VALIDATE issue_number is integer
    VALIDATE comment not empty
    
    payload = {"body": comment}
    
    response = httpx.post(
        f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments",
        headers=auth_headers,
        json=payload
    )
    
    IF response.status_code == 201:
        comment_data = response.json()
        RETURN {
            "status": "success",
            "result": {
                "comment_url": comment_data["html_url"],
                "comment_id": comment_data["id"]
            }
        }
```

**File to Update:**
- `src/tools/github/issues.py` (add new tool function)

**Tool Signature:**
```python
@tool
def post_github_comment(repo_name: str, issue_number: int, comment: str) -> str
```

---

### 2.4 Update Issue Tool ✅ (Close Issue)

**Status:** Partially implemented - `close_github_issue` exists

**Existing Implementation:**
```python
@tool
def close_github_issue(repo_name: str, issue_number: int) -> str
```

**What's Missing:** Full update capability (labels, assignees, milestone)

**To Add:**
```python
@tool
def update_github_issue(repo_name: str, issue_number: int, state: str = None, 
                        labels: str = None, assignees: str = None) -> str
```

**Core Logic:**
```
FUNCTION update_issue(repo, issue_number, state=None, labels=None, assignees=None):
    payload = {}
    IF state: payload["state"] = state  # "open" or "closed"
    IF labels: payload["labels"] = labels.split(",")
    IF assignees: payload["assignees"] = assignees.split(",")
    
    response = httpx.patch(
        f"https://api.github.com/repos/{repo}/issues/{issue_number}",
        headers=auth_headers,
        json=payload
    )
    RETURN formatted_response(response)
```

---

## Phase 3: Repository Operations 🟡 (40% Complete)

**Completed:**
- ✅ list_github_repos
- ✅ get_repo_info  
- ✅ create_github_repo

**Remaining:**
- ⬜ clone_repository (needs GitPython)
- ⬜ create_branch (needs GitPython)
- ⬜ commit_and_push (needs GitPython)

### 3.1 List Repositories Tool ✅

**Status:** Already implemented in `src/tools/github/repos.py`

**Implementation Details:**
- ✅ GET from `/user/repos` and `/search/repositories`
- ✅ Returns formatted list with stats (stars, language)
- ✅ Emoji formatting for better readability

**Existing Implementation:**
```python
@tool
def list_github_repos() -> str
```

**Core Logic:** (Already implemented)
```
FUNCTION list_repositories():
    # Get username
    user_response = httpx.get("https://api.github.com/user", headers=auth_headers)
    username = user_response.json()["login"]
    
    # Search user's repos
    repos_response = httpx.get(f"https://api.github.com/search/repositories?q=user:{username}", ...)
    repos = repos_response.json()["items"]
    
    FORMAT repos with emoji, language, stars
    RETURN formatted string
```

---

### 3.2 Get Repository Info Tool ✅

**Implementation Details:**
- GET from `/repos/{owner}/{repo}`
- Return detailed repository information
- Include branch info, default branch, permissions
- Check if user has write access

**Core Logic:**
```
FUNCTION get_repo_info(repo):
    response = httpx.get(
        f"https://api.github.com/repos/{repo}",
        headers=auth_headers
    )
    
    IF response.status_code == 200:
        repo_data = response.json()
        RETURN {
            "status": "success",
            "result": {
                "name": repo_data["full_name"],
                "description": repo_data["description"],
                "default_branch": repo_data["default_branch"],
                "clone_url": repo_data["clone_url"],
                "ssh_url": repo_data["ssh_url"],
                "permissions": repo_data["permissions"],
                "has_issues": repo_data["has_issues"],
                "has_wiki": repo_data["has_wiki"],
                "visibility": repo_data["visibility"]
            }
        }
```

---

### 3.3 Clone Repository Tool ⬜

**Status:** NOT YET IMPLEMENTED - Need GitPython

**Implementation Details:**
- Use GitPython library for git operations (need to add to pyproject.toml)
- Clone to temporary workspace directory
- Support branch specification
- Handle authentication with token

**Core Logic:**
```
FUNCTION clone_repository(repo_url, branch="main", workspace_dir="/tmp/workspace"):
    repo_name = extract_repo_name(repo_url)
    target_path = f"{workspace_dir}/{repo_name}"
    
    # Inject token into URL for authentication
    authenticated_url = inject_token(repo_url, access_token)
    
    TRY:
        # Clone repository
        git.Repo.clone_from(
            authenticated_url,
            target_path,
            branch=branch,
            depth=1  # Shallow clone for speed
        )
        
        RETURN {
            "status": "success",
            "result": {
                "repo_path": target_path,
                "branch": branch,
                "commit_sha": get_current_commit(target_path)
            }
        }
    CATCH GitCommandError as e:
        RETURN error_response(f"Clone failed: {e}")
```

**Dependencies:**
- GitPython library (ADD TO pyproject.toml: `GitPython>=3.1.0`)
- Secure token handling (use existing github_access_token)

**Files to Create:**
- `src/tools/github/git_ops.py` (NEW FILE for git operations)

---

### 3.4 Create Branch Tool ⬜

**Implementation Details:**
- Create branch from specified base branch
- Use naming convention: feature/*, bugfix/*, hotfix/*
- Push branch to remote
- Return branch name and commit SHA

**Core Logic:**
```
FUNCTION create_branch(repo_path, branch_name, base_branch="main"):
    VALIDATE branch_name follows convention
    
    repo = git.Repo(repo_path)
    
    # Ensure we're on base branch and up to date
    repo.git.checkout(base_branch)
    repo.git.pull()
    
    # Create and checkout new branch
    new_branch = repo.create_head(branch_name)
    new_branch.checkout()
    
    # Push to remote
    origin = repo.remote(name='origin')
    origin.push(branch_name)
    
    RETURN {
        "status": "success",
        "result": {
            "branch": branch_name,
            "base_branch": base_branch,
            "commit_sha": repo.head.commit.hexsha
        }
    }
```

---

### 3.5 Commit and Push Tool ⬜

**Implementation Details:**
- Stage specified files or all changes
- Create commit with conventional commit message
- Push to remote branch
- Handle merge conflicts

**Core Logic:**
```
FUNCTION commit_and_push(repo_path, message, files=None, branch=None):
    repo = git.Repo(repo_path)
    
    # Stage files
    IF files:
        FOR file IN files:
            repo.index.add([file])
    ELSE:
        repo.git.add(A=True)  # Stage all changes
    
    # Check if there are changes to commit
    IF repo.is_dirty() OR repo.untracked_files:
        # Create commit
        commit = repo.index.commit(message)
        
        # Push to remote
        current_branch = repo.active_branch.name
        origin = repo.remote(name='origin')
        
        TRY:
            origin.push(current_branch)
            RETURN {
                "status": "success",
                "result": {
                    "commit_sha": commit.hexsha,
                    "branch": current_branch,
                    "files_changed": len(commit.stats.files)
                }
            }
        CATCH GitCommandError as e:
            RETURN error_response(f"Push failed: {e}")
    ELSE:
        RETURN {
            "status": "success",
            "result": {"message": "No changes to commit"}
        }
```

---

## Phase 4: Pull Request Management ⬜

### 4.1 Create Pull Request Tool ⬜

**Implementation Details:**
- POST to `/repos/{owner}/{repo}/pulls`
- Support draft PRs
- Auto-link related issues
- Request reviewers

**Core Logic:**
```
FUNCTION create_pull_request(repo, title, body, head_branch, base_branch="main", draft=False, reviewers=[]):
    payload = {
        "title": title,
        "body": body,
        "head": head_branch,
        "base": base_branch,
        "draft": draft
    }
    
    response = httpx.post(
        f"https://api.github.com/repos/{repo}/pulls",
        headers=auth_headers,
        json=payload
    )
    
    IF response.status_code == 201:
        pr_data = response.json()
        pr_number = pr_data["number"]
        
        # Request reviewers if specified
        IF reviewers:
            request_reviewers(repo, pr_number, reviewers)
        
        RETURN {
            "status": "success",
            "result": {
                "pr_url": pr_data["html_url"],
                "pr_number": pr_number,
                "state": pr_data["state"]
            }
        }
```

**Files to Create:**
- `src/tools/github/pull_requests.py`

---

### 4.2 List Pull Requests Tool ⬜

**Implementation Details:**
- GET from `/repos/{owner}/{repo}/pulls`
- Filter by state, head, base
- Include review status
- Return formatted PR list

**Core Logic:**
```
FUNCTION list_pull_requests(repo, state="open", head=None, base=None):
    params = {
        "state": state,
        "head": head,
        "base": base,
        "per_page": 30
    }
    
    response = httpx.get(
        f"https://api.github.com/repos/{repo}/pulls",
        headers=auth_headers,
        params=params
    )
    
    IF response.status_code == 200:
        prs = response.json()
        formatted_prs = []
        
        FOR pr IN prs:
            formatted_prs.append({
                "number": pr["number"],
                "title": pr["title"],
                "state": pr["state"],
                "url": pr["html_url"],
                "head": pr["head"]["ref"],
                "base": pr["base"]["ref"],
                "draft": pr["draft"],
                "mergeable": pr["mergeable"],
                "created_at": pr["created_at"]
            })
        
        RETURN success_response(formatted_prs)
```

---

### 4.3 Merge Pull Request Tool ⬜

**Implementation Details:**
- PUT to `/repos/{owner}/{repo}/pulls/{pull_number}/merge`
- Support merge methods: merge, squash, rebase
- Validate PR is mergeable
- Delete branch after merge (optional)

**Core Logic:**
```
FUNCTION merge_pull_request(repo, pr_number, merge_method="squash", delete_branch=True):
    # Check if PR is mergeable
    pr_info = get_pr_info(repo, pr_number)
    
    IF NOT pr_info["mergeable"]:
        RETURN error_response("PR has conflicts or checks failing")
    
    payload = {
        "merge_method": merge_method  # merge, squash, rebase
    }
    
    response = httpx.put(
        f"https://api.github.com/repos/{repo}/pulls/{pr_number}/merge",
        headers=auth_headers,
        json=payload
    )
    
    IF response.status_code == 200:
        merge_data = response.json()
        
        # Delete branch if requested
        IF delete_branch:
            branch_name = pr_info["head"]["ref"]
            delete_branch(repo, branch_name)
        
        RETURN {
            "status": "success",
            "result": {
                "merged": True,
                "sha": merge_data["sha"],
                "message": merge_data["message"]
            }
        }
```

---

## Phase 5: Integration & Error Handling ⬜

### 5.1 Standardized Response Format ⬜

**Implementation Details:**
- Create response builder utility
- Consistent error codes
- Include metadata (timing, API calls)
- Logging integration

**Core Logic:**
```
FUNCTION build_response(status, result=None, error=None, metadata=None):
    response = {
        "status": status,  # "success" or "failure"
        "result": result,
        "error": error,
        "metadata": metadata or {}
    }
    
    # Add timestamp
    response["metadata"]["timestamp"] = datetime.utcnow().isoformat()
    
    # Log response
    log_response(response)
    
    RETURN response

FUNCTION error_response(error_message, error_code=None):
    RETURN build_response(
        status="failure",
        error={
            "message": error_message,
            "code": error_code
        }
    )

FUNCTION success_response(result, metadata=None):
    RETURN build_response(
        status="success",
        result=result,
        metadata=metadata
    )
```

**Files to Create:**
- `src/common/utils/response_builder.py`

---

### 5.2 Rate Limit Handling ⬜

**Implementation Details:**
- Check rate limit headers
- Implement exponential backoff
- Queue requests when near limit
- Return rate limit info in metadata

**Core Logic:**
```
FUNCTION handle_rate_limit(response):
    rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
    rate_limit_reset = response.headers.get("X-RateLimit-Reset")
    
    IF rate_limit_remaining:
        remaining = int(rate_limit_remaining)
        
        IF remaining < 10:
            # Near rate limit, slow down
            reset_time = int(rate_limit_reset)
            wait_time = reset_time - time.time()
            
            IF wait_time > 0:
                log_warning(f"Rate limit low, waiting {wait_time}s")
                time.sleep(wait_time)

FUNCTION retry_with_backoff(func, max_retries=3):
    FOR attempt IN range(max_retries):
        TRY:
            response = func()
            
            IF response.status_code == 403:
                # Check if rate limited
                IF "rate limit" in response.text.lower():
                    handle_rate_limit(response)
                    CONTINUE
            
            RETURN response
            
        CATCH Exception as e:
            IF attempt == max_retries - 1:
                RAISE e
            
            wait_time = 2 ** attempt  # Exponential backoff
            time.sleep(wait_time)
```

**Files to Create:**
- `src/common/utils/rate_limiter.py`

---

### 5.3 Input Validation ⬜

**Implementation Details:**
- Validate repository format (owner/repo)
- Check required fields
- Sanitize user inputs
- Return clear validation errors

**Core Logic:**
```
FUNCTION validate_repo_format(repo):
    pattern = r'^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$'
    
    IF NOT re.match(pattern, repo):
        RAISE ValidationError(f"Invalid repo format: {repo}. Expected: owner/repo")
    
    RETURN True

FUNCTION validate_issue_input(title, body, repo):
    errors = []
    
    IF NOT title OR len(title.strip()) == 0:
        errors.append("Title is required")
    
    IF len(title) > 256:
        errors.append("Title too long (max 256 characters)")
    
    IF NOT validate_repo_format(repo):
        errors.append("Invalid repository format")
    
    IF errors:
        RAISE ValidationError(errors)
    
    RETURN True
```

**Files to Create:**
- `src/common/utils/validators.py`

---

## Phase 6: Testing & Deployment ⬜

### 6.1 Unit Tests ⬜

**Implementation Details:**
- Test each tool independently
- Mock GitHub API responses
- Test error scenarios
- Validate response formats

**Test Cases:**
```
TEST create_issue_success:
    MOCK GitHub API to return 201 with issue data
    CALL create_issue("Test", "Body", "owner/repo")
    ASSERT status == "success"
    ASSERT result contains issue_url and issue_number

TEST create_issue_auth_failure:
    MOCK GitHub API to return 401
    CALL create_issue(...)
    ASSERT status == "failure"
    ASSERT error contains authentication message

TEST list_repos_pagination:
    MOCK GitHub API with 150 repos
    CALL list_repositories(limit=100)
    ASSERT result contains 100 repos
    ASSERT pagination metadata present
```

**Files to Create:**
- `tests/test_git_agent.py`
- `tests/test_github_tools.py`
- `tests/fixtures/github_responses.json`

---

### 6.2 Integration Tests ⬜

**Implementation Details:**
- Test full workflow: create issue → comment → close
- Test git operations: clone → branch → commit → push
- Test PR workflow: create → review → merge
- Use test repository

**Test Scenarios:**
```
TEST full_issue_workflow:
    1. Create issue
    2. Post comment
    3. Update issue state
    4. Verify all operations succeeded

TEST git_workflow:
    1. Clone repository
    2. Create branch
    3. Make changes
    4. Commit and push
    5. Create PR
    6. Verify branch exists on remote
```

---

### 6.2 Deployment Configuration ✅

**Status:** Already deployed to AgentCore Runtime!

**Deployment Command:**
```bash
# Authenticate first
authenticate --to=wealth-dev-au

# Deploy
agentcore launch

# Test
agentcore invoke '{"prompt": "list my repositories"}' --user-id "test-user"
```

**Existing Files:**
- ✅ `.env` (credentials configured)
- ✅ `setup_github_provider.py` (OAuth setup)
- ✅ `README.md` (deployment guide)

---

## Phase 7: Documentation 🟡 (50% Complete)

### 7.1 API Documentation ⬜

**Content:**
- Tool descriptions
- Input/output schemas
- Example requests/responses
- Error codes reference

---

### 7.2 User Guide ⬜

**Content:**
- Setup instructions
- Authentication flow
- Common use cases
- Troubleshooting

---

### 7.3 Developer Guide ⬜

**Content:**
- Architecture overview
- Adding new tools
- Testing guidelines
- Contribution guide

---

## Success Metrics

**Functional Requirements:**
- ✅ Create GitHub issues with markdown formatting
- ✅ Post comments on issues
- ✅ List repositories with filtering
- ✅ Clone repositories to workspace
- ✅ Create branches and commits
- ✅ Create and merge pull requests
- ✅ Handle authentication via OAuth 3LO
- ✅ Rate limit handling with backoff
- ✅ Comprehensive error handling

**Performance Requirements:**
- Issue creation: < 2 seconds
- Repository clone: < 10 seconds (small repos)
- API calls: < 1 second average
- Rate limit: Stay within GitHub limits (5000/hour)

**Security Requirements:**
- Per-user token isolation
- No token exposure in logs
- Secure token storage via AgentCore Identity
- Input sanitization

---

## Dependencies

**Python Packages (Current):**
- ✅ `bedrock-agentcore[strands-agents]>=0.1.0` (AgentCore integration)
- ✅ `bedrock-agentcore-starter-toolkit>=0.1.0` (toolkit)
- ✅ `strands-agents>=0.1.0` (agent framework)
- ✅ `httpx>=0.27.0` (HTTP client)
- ✅ `typer>=0.12.0` (CLI)
- ✅ `python-dotenv>=1.0.0` (environment config)
- ✅ `boto3>=1.39.15` (AWS SDK)

**To Add:**
- ⬜ `GitPython>=3.1.0` (git operations - for clone, branch, commit)
- ⬜ `pydantic>=2.0.0` (data validation - optional)

**AWS Services:**
- Bedrock AgentCore Runtime
- AgentCore Identity (OAuth)
- CloudWatch (logging)
- Secrets Manager (token storage)

**External APIs:**
- GitHub REST API v3
- GitHub OAuth Device Flow

---

## Risk Mitigation

**Risk: Rate Limiting**
- Mitigation: Implement exponential backoff, cache responses, batch operations

**Risk: Authentication Failures**
- Mitigation: Clear error messages, automatic token refresh, fallback to PAT

**Risk: Network Failures**
- Mitigation: Retry logic (3 attempts), timeout handling, graceful degradation

**Risk: Large Repository Clones**
- Mitigation: Shallow clones (depth=1), workspace cleanup, size limits

---

## Future Enhancements (Post-MVP)

- ⬜ GitHub Actions integration
- ⬜ Webhook support for real-time updates
- ⬜ Advanced PR review automation
- ⬜ Repository analytics and insights
- ⬜ Multi-repository operations
- ⬜ GitHub Projects integration
- ⬜ Code search capabilities
- ⬜ Gist management

---

## Timeline Estimate

**Updated Based on Current Progress (Simplified):**

- ✅ **Phase 1:** COMPLETE (Core infrastructure + auth)
- ✅ **Phase 2:** 70% COMPLETE (Issue management - need comment tool) - **0.5 day**
- ⬜ **Phase 3:** 40% COMPLETE (Repos done, need git ops) - **2-3 days**
- ⬜ **Phase 4:** NOT STARTED (Pull request management) - **2-3 days**
- ⬜ **Phase 5:** OPTIONAL (Error handling utilities) - **Skip for MVP**
- ⬜ **Phase 6:** NOT STARTED (Integration testing) - **1 day**
- ⬜ **Phase 7:** NOT STARTED (Documentation) - **1 day**

**Remaining Work: 6.5-8.5 days** (1-1.5 weeks)

**Removed:**
- ❌ Unit tests (no mocks)
- ❌ CLI interface
- ❌ Complex utilities (keep it simple)

**Already Completed:**
- GitHub OAuth 3LO authentication
- AgentCore Runtime deployment
- Repository tools (list, get_info, create)
- Issue tools (list, create, close)
- Base agent structure with Claude 3.5 Sonnet

---

## Notes

- Follow AWS notebook pattern from `runtime_with_strands_and_egress_github_3lo.ipynb`
- Use `@requires_access_token` decorator for all API calls
- Implement tools with `@tool` decorator from Strands
- Keep tools focused and single-purpose
- Prioritize security and user isolation
- Log all operations for debugging
- Handle edge cases gracefully

---

## 🧹 Cleanup (Optional)

**Files to Remove (Not needed for simplified approach):**
```bash
# Remove CLI interface
rm src/agents/github_agent/__main__.py
rm src/agents/github_agent/agent.py

# Keep only runtime.py
```

**Why:**
- CLI not needed (use agentcore invoke)
- agent.py logic moved to runtime.py
- Simpler project structure

---

## 🎯 Next Steps (Priority Order)

### Immediate (1-2 days)
1. **Add post_github_comment tool** to `src/tools/github/issues.py`
   - Simple POST to `/repos/{owner}/{repo}/issues/{issue_number}/comments`
   - Reuse existing httpx pattern

2. **Add GitPython dependency** to `pyproject.toml`
   ```toml
   "GitPython>=3.1.0",
   ```

3. **Create git_ops.py** with clone, branch, commit tools
   - Start with clone_repository (most critical)
   - Then create_branch and commit_and_push

### Short-term (3-5 days)
4. **Pull Request Tools** in `src/tools/github/pull_requests.py`
   - create_pull_request
   - list_pull_requests
   - merge_pull_request

5. **Integration Test Script**
   - `tests/integration/test_github_agent.sh`
   - Real deployment testing
   - AWS authentication integration

### Medium-term (1 week)
6. **Documentation**
   - API reference for all tools
   - Usage examples
   - Integration test guide

---

## 📝 Implementation Checklist

Use this checklist to track your progress:

**Phase 2: Issue Management (70% → 100%)**
- [ ] Add post_github_comment tool
- [ ] Add update_github_issue tool (full update)
- [ ] Update runtime.py to register new tools
- [ ] Test comment posting

**Phase 3: Repository Operations (40% → 100%)**
- [ ] Add GitPython to pyproject.toml
- [ ] Create src/tools/github/git_ops.py
- [ ] Implement clone_repository
- [ ] Implement create_branch
- [ ] Implement commit_and_push
- [ ] Update runtime.py to register git tools
- [ ] Test git operations

**Phase 4: Pull Request Management (0% → 100%)**
- [ ] Create src/tools/github/pull_requests.py
- [ ] Implement create_pull_request
- [ ] Implement list_pull_requests
- [ ] Implement merge_pull_request
- [ ] Update runtime.py to register PR tools
- [ ] Test PR workflow

**Phase 5: Integration & Error Handling (0% → 100%)**
- [ ] Create response_builder.py
- [ ] Create rate_limiter.py
- [ ] Create validators.py
- [ ] Integrate utilities into existing tools
- [ ] Add comprehensive error handling

**Phase 6: Integration Testing (0% → 100%)**
- [ ] Create tests/integration/test_github_agent.sh
- [ ] Create tests/integration/README.md
- [ ] Test list repositories (real API)
- [ ] Test create issue (real API)
- [ ] Test post comment (real API)
- [ ] Test close issue (real API)
- [ ] Test git operations (real repo)
- [ ] Test PR workflow (real PR)
- [ ] Document test setup with authenticate --to=wealth-dev-au

**Phase 7: Documentation (50% → 100%)**
- [ ] Create API documentation
- [ ] Create user guide
- [ ] Create developer guide
- [ ] Update README with new tools
- [ ] Add troubleshooting section

---

## 🚀 Quick Start for Contributors

**To add a new tool:**

1. **Create tool function** in appropriate file:
```python
# src/tools/github/issues.py
@tool
def post_github_comment(repo_name: str, issue_number: int, comment: str) -> str:
    from common.auth import github
    headers = {"Authorization": f"Bearer {github.github_access_token}"}
    response = httpx.post(f"https://api.github.com/repos/{repo_name}/issues/{issue_number}/comments", ...)
    return formatted_response
```

2. **Register in runtime.py:**
```python
from tools.github.issues import post_github_comment
agent = Agent(tools=[..., post_github_comment])
```

3. **Test locally:**
```bash
agentcore launch --local
agentcore invoke '{"prompt": "test"}' --local
```

4. **Deploy:**
```bash
agentcore launch
```

---

**End of Implementation Plan**

**Document Version:** 2.0 (Updated with current project status)  
**Last Updated:** 2024  
**Project:** Multi-Agent Platform - GitHub Agent  
**Status:** 🟡 40% Complete, Deployed to Production
