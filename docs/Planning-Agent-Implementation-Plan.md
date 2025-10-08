# Planning Agent Implementation Plan

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
| Phase 1: Core Infrastructure | ⬜ | 0% | Setup agent structure |
| Phase 2: Requirement Analysis | ⬜ | 0% | Extract & parse requirements |
| Phase 3: Plan Generation | ⬜ | 0% | LLM integration for plans |
| Phase 4: Plan Validation | ⬜ | 0% | Validate & optimize plans |
| Phase 5: Error Handling | ⬜ | 0% | Inline error handling |
| Phase 6: Integration Testing | ⬜ | 0% | Real tests only |
| Phase 7: Documentation | ⬜ | 0% | API docs |

**Simplified Approach:**
- ❌ No CLI interface
- ❌ No unit tests with mocks
- ✅ Only real integration tests
- ✅ Focus on core features

---

## 🎯 Quick Reference

**What Needs to Be Built:**
```bash
# Deploy the planning agent
authenticate --to=wealth-dev-au
agentcore launch

# Invoke the agent
agentcore invoke '{"prompt": "Create a plan for implementing user authentication"}' --user-id "user-123"
```

**Core Functionality:**
1. Extract requirements from JIRA tickets or user input
2. Generate step-by-step implementation plans using LLM
3. Validate plan structure and dependencies
4. Return formatted markdown plans

**What's Missing:**
- Everything (agent not started yet)

**Simplified Approach:**
- ❌ No complex orchestrator
- ❌ No response_builder utilities
- ✅ Direct LLM integration (Claude via Bedrock)
- ✅ Simple inline validation

---

## Overview

The Planning Agent is responsible for analyzing requirements and generating detailed implementation plans. It takes JIRA tickets or user requests as input and produces structured, actionable plans that other agents can execute.

**Key Responsibilities:**
- Parse requirements from various sources (JIRA, user input)
- Generate step-by-step implementation plans
- Identify files to modify and dependencies
- Estimate effort and complexity
- Format plans as markdown for GitHub issues

---

## Phase 1: Core Infrastructure ⬜

### 1.1 Agent Setup ⬜

**Implementation Details:**
- Create BedrockAgentCoreApp entrypoint
- Configure Claude 3.5 Sonnet model
- Define planning tools
- Set up system prompt

**Files to Create:**
- `src/agents/planning_agent/runtime.py` - AgentCore entrypoint
- `src/tools/planning/` - Planning tools directory

**Core Logic:**
```
CLASS PlanningAgent:
    PROPERTIES:
        - model: Claude 3.5 Sonnet
        - tools: [analyze_requirements, generate_plan, validate_plan]
        - max_tokens: 4000 (for detailed plans)
    
    METHOD handle_request(payload):
        requirements = payload.get("requirements")
        context = payload.get("context", {})
        
        ANALYZE requirements
        GENERATE plan using LLM
        VALIDATE plan structure
        FORMAT as markdown
        RETURN plan
```

**System Prompt:**
```
You are a Planning Agent specialized in creating detailed implementation plans for software development tasks.

Your responsibilities:
1. Analyze requirements from JIRA tickets or user descriptions
2. Break down complex tasks into actionable steps
3. Identify files to create/modify
4. Specify dependencies between steps
5. Estimate effort and complexity

Guidelines:
- Create clear, sequential steps
- Each step should be specific and actionable
- Include technical details (APIs, libraries, patterns)
- Consider edge cases and error handling
- Format output as structured markdown

Input Format:
{
    "requirements": "User story or JIRA ticket description",
    "context": {
        "repo": "owner/repo",
        "language": "python",
        "framework": "fastapi"
    }
}

Output Format:
Return a detailed implementation plan in markdown with:
- Title
- Overview
- Prerequisites
- Implementation Steps (numbered, with details)
- Files to Create/Modify
- Testing Strategy
- Estimated Effort
```

---

## Phase 2: Requirement Analysis ⬜

### 2.1 Parse Requirements Tool ⬜

**Implementation Details:**
- Extract key information from text
- Identify technical requirements
- Parse acceptance criteria
- Detect constraints

**Core Logic:**
```
FUNCTION parse_requirements(input_text, context):
    # Extract structured data
    requirements = {
        "title": extract_title(input_text),
        "description": extract_description(input_text),
        "acceptance_criteria": extract_criteria(input_text),
        "technical_requirements": identify_tech_requirements(input_text),
        "constraints": identify_constraints(input_text)
    }
    
    # Add context
    requirements["context"] = context
    
    RETURN requirements
```

**Tool Signature:**
```python
@tool
def parse_requirements(input_text: str, repo: str = None, language: str = None) -> str
```

**Example Input:**
```
"Implement user authentication with JWT tokens. 
Users should be able to register, login, and logout. 
Passwords must be hashed. Session timeout after 30 minutes."
```

**Example Output:**
```json
{
    "title": "Implement User Authentication",
    "description": "JWT-based authentication system",
    "acceptance_criteria": [
        "Users can register with email/password",
        "Users can login and receive JWT token",
        "Users can logout",
        "Passwords are hashed",
        "Sessions expire after 30 minutes"
    ],
    "technical_requirements": [
        "JWT library",
        "Password hashing (bcrypt)",
        "Session management",
        "Database for users"
    ],
    "constraints": [
        "30 minute session timeout",
        "Secure password storage"
    ]
}
```

---

### 2.2 Analyze Complexity Tool ⬜

**Implementation Details:**
- Estimate task complexity (simple/medium/complex)
- Identify required skills
- Detect potential blockers
- Estimate effort

**Core Logic:**
```
FUNCTION analyze_complexity(requirements):
    complexity_score = 0
    
    # Count acceptance criteria
    complexity_score += len(requirements["acceptance_criteria"]) * 2
    
    # Check technical requirements
    IF "database" in requirements:
        complexity_score += 5
    IF "authentication" in requirements:
        complexity_score += 5
    IF "API integration" in requirements:
        complexity_score += 3
    
    # Determine complexity level
    IF complexity_score < 10:
        level = "simple"
        effort = "1-2 hours"
    ELIF complexity_score < 20:
        level = "medium"
        effort = "3-6 hours"
    ELSE:
        level = "complex"
        effort = "1-2 days"
    
    RETURN {
        "complexity": level,
        "estimated_effort": effort,
        "score": complexity_score
    }
```

---

## Phase 3: Plan Generation ⬜

### 3.1 Generate Plan Tool ⬜

**Implementation Details:**
- Use Claude 3.5 Sonnet via Bedrock
- Structured prompt engineering
- JSON output parsing
- Markdown formatting

**Core Logic:**
```
FUNCTION generate_plan(requirements, context):
    # Build prompt
    prompt = f"""
    Create a detailed implementation plan for:
    
    Title: {requirements["title"]}
    Description: {requirements["description"]}
    
    Acceptance Criteria:
    {format_criteria(requirements["acceptance_criteria"])}
    
    Context:
    - Repository: {context.get("repo")}
    - Language: {context.get("language")}
    - Framework: {context.get("framework")}
    
    Provide a step-by-step plan with:
    1. Prerequisites
    2. Implementation steps (detailed)
    3. Files to create/modify
    4. Testing approach
    5. Estimated effort
    
    Format as markdown.
    """
    
    # Call LLM
    response = bedrock_client.invoke_model(
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",
        prompt=prompt,
        max_tokens=4000,
        temperature=0.3
    )
    
    plan_text = response["content"]
    
    # Validate and format
    validated_plan = validate_plan_structure(plan_text)
    
    RETURN validated_plan
```

**Tool Signature:**
```python
@tool
def generate_implementation_plan(requirements: str, repo: str = None, language: str = None) -> str
```

**Example Output:**
```markdown
# Implementation Plan: User Authentication

## Overview
Implement JWT-based authentication system with user registration, login, and session management.

## Prerequisites
- FastAPI framework installed
- PostgreSQL database setup
- python-jose library for JWT
- passlib for password hashing

## Implementation Steps

### Step 1: Database Schema
**Action:** Create user table
**Details:**
- Create `models/user.py`
- Define User model with fields: id, email, hashed_password, created_at
- Add database migration

**Files to Create:**
- `models/user.py`
- `alembic/versions/001_create_users.py`

### Step 2: Password Hashing
**Action:** Implement password utilities
**Details:**
- Create `utils/security.py`
- Add `hash_password()` function using bcrypt
- Add `verify_password()` function

**Files to Create:**
- `utils/security.py`

### Step 3: JWT Token Generation
**Action:** Implement JWT utilities
**Details:**
- Add `create_access_token()` function
- Add `decode_token()` function
- Set 30-minute expiration

**Files to Modify:**
- `utils/security.py`

### Step 4: Registration Endpoint
**Action:** Create user registration API
**Details:**
- Create `POST /auth/register` endpoint
- Validate email format
- Hash password before storing
- Return user ID

**Files to Create:**
- `routers/auth.py`

### Step 5: Login Endpoint
**Action:** Create login API
**Details:**
- Create `POST /auth/login` endpoint
- Verify credentials
- Generate JWT token
- Return token

**Files to Modify:**
- `routers/auth.py`

### Step 6: Logout Endpoint
**Action:** Create logout API
**Details:**
- Create `POST /auth/logout` endpoint
- Invalidate token (add to blacklist)
- Return success message

**Files to Modify:**
- `routers/auth.py`

### Step 7: Authentication Middleware
**Action:** Protect routes with auth
**Details:**
- Create `dependencies/auth.py`
- Add `get_current_user()` dependency
- Verify JWT token
- Check expiration

**Files to Create:**
- `dependencies/auth.py`

### Step 8: Testing
**Action:** Write comprehensive tests
**Details:**
- Test registration with valid/invalid data
- Test login with correct/incorrect credentials
- Test token expiration
- Test protected endpoints

**Files to Create:**
- `tests/test_auth.py`

## Files Summary

**To Create:**
- `models/user.py`
- `utils/security.py`
- `routers/auth.py`
- `dependencies/auth.py`
- `tests/test_auth.py`
- `alembic/versions/001_create_users.py`

**To Modify:**
- `main.py` (register auth router)
- `requirements.txt` (add dependencies)

## Testing Strategy
1. Unit tests for password hashing
2. Unit tests for JWT generation/validation
3. Integration tests for auth endpoints
4. Test token expiration
5. Test invalid credentials

## Estimated Effort
**Total: 4-6 hours**
- Database setup: 30 minutes
- Core auth logic: 2 hours
- API endpoints: 1.5 hours
- Testing: 1.5 hours
- Documentation: 30 minutes

## Dependencies
```
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.5
```
```

---

### 3.2 Format Plan Tool ⬜

**Implementation Details:**
- Convert LLM output to structured format
- Add markdown formatting
- Include code snippets where helpful
- Add checkboxes for tracking

**Core Logic:**
```
FUNCTION format_plan_as_markdown(plan_data):
    markdown = f"# {plan_data['title']}\n\n"
    
    # Overview
    markdown += f"## Overview\n{plan_data['overview']}\n\n"
    
    # Prerequisites
    markdown += "## Prerequisites\n"
    FOR prereq IN plan_data['prerequisites']:
        markdown += f"- {prereq}\n"
    markdown += "\n"
    
    # Steps
    markdown += "## Implementation Steps\n\n"
    FOR step IN plan_data['steps']:
        markdown += f"### Step {step['number']}: {step['title']}\n"
        markdown += f"**Action:** {step['action']}\n"
        markdown += f"**Details:**\n{step['details']}\n\n"
        
        IF step['files']:
            markdown += "**Files:**\n"
            FOR file IN step['files']:
                markdown += f"- `{file}`\n"
            markdown += "\n"
    
    # Files summary
    markdown += "## Files Summary\n\n"
    markdown += "**To Create:**\n"
    FOR file IN plan_data['files_to_create']:
        markdown += f"- [ ] `{file}`\n"
    
    # Effort estimate
    markdown += f"\n## Estimated Effort\n{plan_data['effort']}\n"
    
    RETURN markdown
```

---

## Phase 4: Plan Validation ⬜

### 4.1 Validate Plan Structure ⬜

**Implementation Details:**
- Check required sections exist
- Validate step dependencies
- Ensure files are specified
- Verify effort estimates

**Core Logic:**
```
FUNCTION validate_plan_structure(plan_text):
    errors = []
    
    # Check required sections
    required_sections = ["Overview", "Implementation Steps", "Files", "Estimated Effort"]
    FOR section IN required_sections:
        IF section NOT IN plan_text:
            errors.append(f"Missing section: {section}")
    
    # Validate steps
    steps = extract_steps(plan_text)
    IF len(steps) == 0:
        errors.append("No implementation steps found")
    
    # Check file specifications
    IF "Files to Create" NOT IN plan_text AND "Files to Modify" NOT IN plan_text:
        errors.append("No files specified")
    
    # Inline validation - return error message if invalid
    IF errors:
        RETURN f"❌ Invalid plan:\n" + "\n".join(errors)
    
    RETURN plan_text
```

---

### 4.2 Optimize Plan ⬜

**Implementation Details:**
- Identify parallelizable steps
- Group related file modifications
- Merge redundant operations
- Optimize step order

**Core Logic:**
```
FUNCTION optimize_plan(plan):
    optimized_steps = []
    
    # Group file operations
    file_groups = group_by_file(plan['steps'])
    
    # Identify parallel steps (no dependencies)
    parallel_groups = identify_parallel_steps(plan['steps'])
    
    # Reorder for efficiency
    FOR group IN parallel_groups:
        IF can_parallelize(group):
            optimized_steps.append({
                "type": "parallel",
                "steps": group
            })
        ELSE:
            optimized_steps.extend(group)
    
    plan['optimized_steps'] = optimized_steps
    RETURN plan
```

---

## Phase 5: Error Handling (Simplified) ⬜

### 5.1 Inline Error Handling

**Approach:** Keep error handling simple and inline

**Example:**
```python
@tool
def generate_implementation_plan(requirements: str, repo: str = None) -> str:
    # Inline validation
    if not requirements or len(requirements.strip()) < 10:
        return "❌ Error: Requirements too short. Please provide detailed requirements."
    
    try:
        # Generate plan
        plan = call_llm_for_plan(requirements, repo)
        
        # Validate
        if not validate_plan_structure(plan):
            return "❌ Error: Generated plan is invalid. Please try again."
        
        return plan
        
    except Exception as e:
        return f"❌ Error generating plan: {str(e)}"
```

**Why no complex utilities:**
- LLM calls are simple (one API call)
- Validation is straightforward
- Keep it inline and readable

---

## Phase 6: Integration Testing ⬜

### 6.1 Integration Tests Only

**Test Script:** `tests/integration/test_planning_agent.sh`

```bash
#!/bin/bash
# Integration tests for Planning Agent

authenticate --to=wealth-dev-au

USER_ID="test-user-$(date +%s)"
AGENT_ARN="arn:aws:bedrock-agentcore:ap-southeast-2:xxx:agent/planning-agent"

# Test 1: Simple plan generation
echo "Test 1: Generate simple plan"
agentcore invoke '{
    "prompt": "Create a plan for adding a health check endpoint to a FastAPI app"
}' --user-id "$USER_ID" --agent-arn "$AGENT_ARN"

# Test 2: Complex plan with context
echo "Test 2: Generate complex plan with context"
agentcore invoke '{
    "prompt": "Create a plan for implementing user authentication",
    "context": {
        "repo": "myorg/myapp",
        "language": "python",
        "framework": "fastapi"
    }
}' --user-id "$USER_ID" --agent-arn "$AGENT_ARN"

# Test 3: Plan from JIRA-style input
echo "Test 3: Generate plan from JIRA ticket"
agentcore invoke '{
    "prompt": "As a user, I want to reset my password via email so that I can regain access to my account. Acceptance criteria: 1) User receives reset link via email, 2) Link expires after 1 hour, 3) Password must meet complexity requirements"
}' --user-id "$USER_ID" --agent-arn "$AGENT_ARN"
```

---

## Phase 7: Documentation ⬜

### 7.1 API Documentation

**Content:**
- Tool descriptions
- Input/output examples
- Prompt engineering tips
- Best practices

---

## Timeline Estimate

**Total: 3-4 days**

- ✅ **Phase 1:** Agent setup (0.5 day)
- ⬜ **Phase 2:** Requirement analysis (0.5 day)
- ⬜ **Phase 3:** Plan generation with LLM (1 day)
- ⬜ **Phase 4:** Plan validation (0.5 day)
- ⬜ **Phase 5:** Error handling (0.5 day)
- ⬜ **Phase 6:** Integration testing (0.5 day)
- ⬜ **Phase 7:** Documentation (0.5 day)

---

## Dependencies

**Python Packages:**
- ✅ `bedrock-agentcore[strands-agents]>=0.1.0`
- ✅ `strands-agents>=0.1.0`
- ✅ `boto3>=1.39.15` (for Bedrock)
- ✅ `httpx>=0.27.0`

**AWS Services:**
- Bedrock AgentCore Runtime
- Bedrock (Claude 3.5 Sonnet)
- CloudWatch (logging)

**No Additional Dependencies Needed:**
- ❌ No GitPython (planning only, no git ops)
- ❌ No OAuth (no external API access)
- ❌ No database (stateless agent)

---

## Success Metrics

**Functional Requirements:**
- ✅ Parse requirements from text input
- ✅ Generate detailed implementation plans
- ✅ Include file specifications
- ✅ Provide effort estimates
- ✅ Format as markdown
- ✅ Validate plan structure

**Quality Requirements:**
- Plans should be actionable (specific steps)
- Steps should be in logical order
- File paths should be realistic
- Effort estimates should be reasonable
- Markdown should be well-formatted

---

## 🎯 Next Steps (Priority Order)

### Immediate (Day 1)
1. **Create agent structure**
   - `src/agents/planning_agent/runtime.py`
   - Define system prompt
   - Set up Bedrock model

2. **Create basic tool**
   - `src/tools/planning/plan_generator.py`
   - Simple LLM call
   - Basic validation

### Short-term (Days 2-3)
3. **Enhance plan generation**
   - Better prompt engineering
   - Structured output parsing
   - Markdown formatting

4. **Add validation**
   - Check plan structure
   - Validate steps
   - Inline error handling

### Final (Day 4)
5. **Integration testing**
   - Create test script
   - Test with real requirements
   - Verify output quality

6. **Documentation**
   - Usage examples
   - Prompt tips
   - Best practices

---

## 📝 Implementation Checklist

**Phase 1: Core Infrastructure (0% → 100%)**
- [ ] Create `src/agents/planning_agent/runtime.py`
- [ ] Create `src/tools/planning/` directory
- [ ] Define system prompt
- [ ] Configure Claude 3.5 Sonnet model
- [ ] Test basic agent invocation

**Phase 2: Requirement Analysis (0% → 100%)**
- [ ] Create `parse_requirements` tool
- [ ] Extract title, description, criteria
- [ ] Identify technical requirements
- [ ] Add complexity analysis

**Phase 3: Plan Generation (0% → 100%)**
- [ ] Create `generate_plan` tool
- [ ] Build LLM prompt template
- [ ] Call Bedrock API
- [ ] Parse LLM response
- [ ] Format as markdown

**Phase 4: Plan Validation (0% → 100%)**
- [ ] Create `validate_plan` function
- [ ] Check required sections
- [ ] Validate step structure
- [ ] Verify file specifications
- [ ] Inline error messages

**Phase 5: Error Handling (0% → 100%)**
- [ ] Add input validation
- [ ] Handle LLM errors
- [ ] Handle parsing errors
- [ ] Return clear error messages

**Phase 6: Integration Testing (0% → 100%)**
- [ ] Create `tests/integration/test_planning_agent.sh`
- [ ] Test simple plans
- [ ] Test complex plans
- [ ] Test error cases
- [ ] Verify output quality

**Phase 7: Documentation (0% → 100%)**
- [ ] Write API documentation
- [ ] Add usage examples
- [ ] Document prompt engineering
- [ ] Add troubleshooting guide

---

## Notes

- Focus on LLM prompt engineering for quality plans
- Keep validation simple and inline
- No complex orchestration needed
- Plans should be human-readable markdown
- Test with real-world requirements

---

**End of Implementation Plan**

**Document Version:** 1.0  
**Status:** ⬜ Not Started  
**Estimated Effort:** 3-4 days
