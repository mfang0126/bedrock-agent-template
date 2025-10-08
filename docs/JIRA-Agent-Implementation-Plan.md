# JIRA Agent Implementation Plan

**Status Legend:**
- ⬜ Not Started
- 🟡 In Progress
- ✅ Completed
- ❌ Blocked

**Last Updated:** 2024

**Project Location:** `/Users/ming.fang/Code/ai-coding-agents/app`

---

## 📊 Implementation Progress

**Overall Status:** ⬜ 0% Complete (Not Started)

| Phase | Status | Progress | Remaining Work |
|-------|--------|----------|----------------|
| Phase 1: Core Infrastructure | ⬜ | 0% | Setup agent + OAuth |
| Phase 2: Ticket Operations | ⬜ | 0% | Fetch, parse tickets |
| Phase 3: Status Updates | ⬜ | 0% | Update status, comments |
| Phase 4: Integration | ⬜ | 0% | Link to GitHub |
| Phase 5: Error Handling | ⬜ | 0% | Inline validation |
| Phase 6: Integration Testing | ⬜ | 0% | Real JIRA tests |
| Phase 7: Documentation | ⬜ | 0% | API docs |

**Simplified Approach:**
- ❌ No CLI interface
- ❌ No unit tests with mocks
- ✅ Only real integration tests
- ✅ JIRA REST API via httpx

---

## 🎯 Quick Reference

**What Needs to Be Built:**
```bash
# Deploy the JIRA agent
authenticate --to=wealth-dev-au
agentcore launch

# Invoke the agent
agentcore invoke '{"prompt": "Get details for JIRA-123"}' --user-id "user-123"
```

**Core Functionality:**
1. Fetch JIRA ticket details
2. Extract requirements and acceptance criteria
3. Update ticket status
4. Add comments to tickets
5. Link GitHub issues to JIRA

**Authentication:**
- JIRA API Token (stored in AgentCore Identity)
- Similar OAuth pattern to GitHub Agent

---

## Overview

The JIRA Agent integrates with JIRA to fetch ticket details, extract requirements, and update ticket status. It acts as the bridge between JIRA project management and the development workflow.

**Key Responsibilities:**
- Fetch ticket details (title, description, acceptance criteria)
- Parse requirements for Planning Agent
- Update ticket status (In Progress, Done, etc.)
- Add comments with execution results
- Link GitHub issues to JIRA tickets

---

## Phase 1: Core Infrastructure ⬜

### 1.1 Authentication Setup ⬜

**Implementation Details:**
- JIRA API Token authentication
- Store credentials in AgentCore Identity
- Support both Cloud and Server JIRA

**Files to Create:**
- `src/common/auth/jira.py` - JIRA auth
- `src/common/config/jira_config.py` - JIRA configuration
- `setup_jira_provider.py` - Provider setup script

**Core Logic:**
```
FUNCTION authenticate_jira(user_id):
    # Get JIRA credentials from AgentCore Identity
    jira_url = get_config("JIRA_URL")
    api_token = get_token_from_identity(user_id, "jira-provider")
    email = get_config("JIRA_EMAIL")
    
    # Create auth header
    auth = base64_encode(f"{email}:{api_token}")
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    
    RETURN headers, jira_url
```

**Environment Variables:**
```bash
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your_api_token
```

---

### 1.2 Agent Setup ⬜

**Files to Create:**
- `src/agents/jira_agent/runtime.py` - AgentCore entrypoint
- `src/tools/jira/` - JIRA tools directory

**System Prompt:**
```
You are a JIRA Agent specialized in fetching and managing JIRA tickets.

Your responsibilities:
1. Fetch ticket details from JIRA
2. Extract requirements and acceptance criteria
3. Update ticket status
4. Add comments to tickets
5. Link GitHub issues to JIRA

Guidelines:
- Always validate ticket IDs (format: PROJECT-123)
- Extract structured data from ticket descriptions
- Handle JIRA API errors gracefully
- Return formatted, readable responses

Input Format:
{
    "action": "fetch_ticket|update_status|add_comment",
    "ticket_id": "JIRA-123",
    "payload": {...}
}

Output Format:
Return structured data or success/error messages
```

---

## Phase 2: Ticket Operations ⬜

### 2.1 Fetch Ticket Tool ⬜

**Implementation Details:**
- GET from `/rest/api/3/issue/{issueKey}`
- Parse ticket fields
- Extract acceptance criteria
- Format for Planning Agent

**Core Logic:**
```
FUNCTION fetch_ticket(ticket_id):
    # Validate ticket ID format
    IF NOT re.match(r'^[A-Z]+-\d+$', ticket_id):
        RETURN "❌ Invalid ticket ID format. Expected: PROJECT-123"
    
    # Fetch from JIRA API
    headers, jira_url = authenticate_jira()
    response = httpx.get(
        f"{jira_url}/rest/api/3/issue/{ticket_id}",
        headers=headers
    )
    
    IF response.status_code == 200:
        ticket = response.json()
        
        # Extract key fields
        result = {
            "ticket_id": ticket_id,
            "title": ticket["fields"]["summary"],
            "description": ticket["fields"]["description"],
            "status": ticket["fields"]["status"]["name"],
            "priority": ticket["fields"]["priority"]["name"],
            "assignee": ticket["fields"]["assignee"]["displayName"] if ticket["fields"]["assignee"] else None,
            "acceptance_criteria": extract_acceptance_criteria(ticket["fields"]["description"]),
            "labels": ticket["fields"]["labels"],
            "sprint": extract_sprint(ticket["fields"])
        }
        
        RETURN format_ticket_details(result)
    ELSE:
        RETURN f"❌ Error fetching ticket: {response.status_code}"
```

**Tool Signature:**
```python
@tool
def fetch_jira_ticket(ticket_id: str) -> str
```

**Example Output:**
```
📋 JIRA-123: Implement User Authentication

**Status:** To Do
**Priority:** High
**Assignee:** John Doe
**Sprint:** Sprint 24

**Description:**
As a user, I want to authenticate with email and password so that I can access the system securely.

**Acceptance Criteria:**
✓ Users can register with email/password
✓ Passwords are hashed using bcrypt
✓ JWT tokens are issued on login
✓ Sessions expire after 30 minutes
✓ Users can logout

**Labels:** backend, security, authentication
```

---

### 2.2 Parse Requirements Tool ⬜

**Implementation Details:**
- Extract structured requirements from ticket
- Identify technical requirements
- Parse acceptance criteria
- Format for Planning Agent

**Core Logic:**
```
FUNCTION parse_ticket_requirements(ticket_data):
    requirements = {
        "title": ticket_data["title"],
        "description": ticket_data["description"],
        "acceptance_criteria": ticket_data["acceptance_criteria"],
        "priority": ticket_data["priority"],
        "technical_requirements": []
    }
    
    # Extract technical requirements from description
    description_lower = ticket_data["description"].lower()
    
    IF "database" in description_lower OR "db" in description_lower:
        requirements["technical_requirements"].append("database")
    
    IF "api" in description_lower:
        requirements["technical_requirements"].append("api")
    
    IF "auth" in description_lower OR "authentication" in description_lower:
        requirements["technical_requirements"].append("authentication")
    
    RETURN requirements
```

---

## Phase 3: Status Updates ⬜

### 3.1 Update Ticket Status Tool ⬜

**Implementation Details:**
- POST to `/rest/api/3/issue/{issueKey}/transitions`
- Support common transitions (To Do → In Progress → Done)
- Validate transition is allowed

**Core Logic:**
```
FUNCTION update_ticket_status(ticket_id, new_status):
    # Get available transitions
    headers, jira_url = authenticate_jira()
    transitions_response = httpx.get(
        f"{jira_url}/rest/api/3/issue/{ticket_id}/transitions",
        headers=headers
    )
    
    transitions = transitions_response.json()["transitions"]
    
    # Find matching transition
    transition_id = None
    FOR transition IN transitions:
        IF transition["name"].lower() == new_status.lower():
            transition_id = transition["id"]
            BREAK
    
    IF NOT transition_id:
        RETURN f"❌ Cannot transition to '{new_status}'. Available: {[t['name'] for t in transitions]}"
    
    # Execute transition
    response = httpx.post(
        f"{jira_url}/rest/api/3/issue/{ticket_id}/transitions",
        headers=headers,
        json={"transition": {"id": transition_id}}
    )
    
    IF response.status_code == 204:
        RETURN f"✅ Ticket {ticket_id} moved to '{new_status}'"
    ELSE:
        RETURN f"❌ Error updating status: {response.text}"
```

**Tool Signature:**
```python
@tool
def update_jira_status(ticket_id: str, status: str) -> str
```

---

### 3.2 Add Comment Tool ⬜

**Implementation Details:**
- POST to `/rest/api/3/issue/{issueKey}/comment`
- Support markdown formatting
- Link to GitHub issues

**Core Logic:**
```
FUNCTION add_jira_comment(ticket_id, comment, github_issue_url=None):
    headers, jira_url = authenticate_jira()
    
    # Format comment with GitHub link if provided
    comment_body = comment
    IF github_issue_url:
        comment_body += f"\n\n🔗 GitHub Issue: {github_issue_url}"
    
    response = httpx.post(
        f"{jira_url}/rest/api/3/issue/{ticket_id}/comment",
        headers=headers,
        json={"body": comment_body}
    )
    
    IF response.status_code == 201:
        comment_data = response.json()
        RETURN f"✅ Comment added to {ticket_id}"
    ELSE:
        RETURN f"❌ Error adding comment: {response.text}"
```

**Tool Signature:**
```python
@tool
def add_jira_comment(ticket_id: str, comment: str, github_url: str = None) -> str
```

---

## Phase 4: Integration ⬜

### 4.1 Link GitHub Issue Tool ⬜

**Implementation Details:**
- Add GitHub issue link to JIRA ticket
- Update JIRA custom field or add to description
- Create bidirectional link

**Core Logic:**
```
FUNCTION link_github_issue(ticket_id, github_issue_url):
    headers, jira_url = authenticate_jira()
    
    # Add as remote link
    response = httpx.post(
        f"{jira_url}/rest/api/3/issue/{ticket_id}/remotelink",
        headers=headers,
        json={
            "object": {
                "url": github_issue_url,
                "title": "GitHub Issue",
                "icon": {
                    "url16x16": "https://github.com/favicon.ico"
                }
            }
        }
    )
    
    IF response.status_code == 201:
        RETURN f"✅ Linked GitHub issue to {ticket_id}"
    ELSE:
        RETURN f"❌ Error linking: {response.text}"
```

---

## Phase 5: Error Handling (Simplified) ⬜

**Approach:** Inline error handling

**Example:**
```python
@tool
def fetch_jira_ticket(ticket_id: str) -> str:
    # Inline validation
    if not ticket_id or not re.match(r'^[A-Z]+-\d+$', ticket_id):
        return "❌ Invalid ticket ID. Format: PROJECT-123"
    
    try:
        headers, jira_url = get_jira_auth()
        response = httpx.get(f"{jira_url}/rest/api/3/issue/{ticket_id}", headers=headers)
        
        if response.status_code == 404:
            return f"❌ Ticket {ticket_id} not found"
        elif response.status_code == 401:
            return "❌ Authentication failed. Check JIRA credentials"
        elif response.status_code != 200:
            return f"❌ JIRA API error: {response.status_code}"
        
        return format_ticket(response.json())
        
    except Exception as e:
        return f"❌ Error: {str(e)}"
```

---

## Phase 6: Integration Testing ⬜

**Test Script:** `tests/integration/test_jira_agent.sh`

```bash
#!/bin/bash
# Integration tests for JIRA Agent

authenticate --to=wealth-dev-au

USER_ID="test-user-$(date +%s)"
AGENT_ARN="arn:aws:bedrock-agentcore:ap-southeast-2:xxx:agent/jira-agent"
TEST_TICKET="PROJ-123"

# Test 1: Fetch ticket
echo "Test 1: Fetch JIRA ticket"
agentcore invoke "{\"prompt\": \"Get details for ${TEST_TICKET}\"}" \
  --user-id "$USER_ID" \
  --agent-arn "$AGENT_ARN"

# Test 2: Update status
echo "Test 2: Update ticket status"
agentcore invoke "{\"prompt\": \"Move ${TEST_TICKET} to In Progress\"}" \
  --user-id "$USER_ID" \
  --agent-arn "$AGENT_ARN"

# Test 3: Add comment
echo "Test 3: Add comment to ticket"
agentcore invoke "{\"prompt\": \"Add comment to ${TEST_TICKET}: Implementation started\"}" \
  --user-id "$USER_ID" \
  --agent-arn "$AGENT_ARN"
```

---

## Timeline Estimate

**Total: 2-3 days**

- ⬜ **Phase 1:** Authentication + agent setup (0.5 day)
- ⬜ **Phase 2:** Ticket operations (0.5 day)
- ⬜ **Phase 3:** Status updates (0.5 day)
- ⬜ **Phase 4:** GitHub integration (0.5 day)
- ⬜ **Phase 5:** Error handling (0.5 day)
- ⬜ **Phase 6:** Integration testing (0.5 day)
- ⬜ **Phase 7:** Documentation (0.5 day)

---

## Dependencies

**Python Packages:**
- ✅ `httpx>=0.27.0` (HTTP client)
- ✅ `bedrock-agentcore[strands-agents]>=0.1.0`
- ✅ `python-dotenv>=1.0.0`

**No Additional Dependencies:**
- ❌ No special JIRA library (use httpx directly)
- ❌ No OAuth (API token auth)

**External APIs:**
- JIRA REST API v3
- JIRA Cloud or Server

---

## Success Metrics

**Functional Requirements:**
- ✅ Fetch ticket details
- ✅ Parse requirements
- ✅ Update ticket status
- ✅ Add comments
- ✅ Link GitHub issues

**Quality Requirements:**
- Ticket data should be complete
- Status transitions should be valid
- Comments should be formatted
- Links should be bidirectional

---

## 📝 Implementation Checklist

**Phase 1: Core Infrastructure (0% → 100%)**
- [ ] Create `src/agents/jira_agent/runtime.py`
- [ ] Create `src/tools/jira/` directory
- [ ] Set up JIRA authentication
- [ ] Create `setup_jira_provider.py`
- [ ] Test basic connection

**Phase 2: Ticket Operations (0% → 100%)**
- [ ] Create `fetch_jira_ticket` tool
- [ ] Parse ticket fields
- [ ] Extract acceptance criteria
- [ ] Format output

**Phase 3: Status Updates (0% → 100%)**
- [ ] Create `update_jira_status` tool
- [ ] Get available transitions
- [ ] Execute transition
- [ ] Create `add_jira_comment` tool

**Phase 4: Integration (0% → 100%)**
- [ ] Create `link_github_issue` tool
- [ ] Add remote links
- [ ] Test bidirectional linking

**Phase 5: Error Handling (0% → 100%)**
- [ ] Add input validation
- [ ] Handle API errors
- [ ] Return clear messages

**Phase 6: Integration Testing (0% → 100%)**
- [ ] Create test script
- [ ] Test with real JIRA instance
- [ ] Verify all operations

**Phase 7: Documentation (0% → 100%)**
- [ ] Write API documentation
- [ ] Add usage examples
- [ ] Document setup process

---

**End of Implementation Plan**

**Document Version:** 1.0  
**Status:** ⬜ Not Started  
**Estimated Effort:** 2-3 days
