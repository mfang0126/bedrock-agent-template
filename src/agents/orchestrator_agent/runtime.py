"""
Orchestrator Agent Runtime

Coordinates multiple specialized agents to execute end-to-end workflows.
Parses user requests, determines workflow sequence, and coordinates agent execution.
"""

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
from src.tools.orchestrator import (
    parse_user_request,
    determine_workflow,
    execute_workflow_sequence,
)


app = BedrockAgentCoreApp()

# Use Claude 3.5 Sonnet
MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
REGION = "ap-southeast-2"

model = BedrockModel(model_id=MODEL_ID, region_name=REGION)

# System prompt for Orchestrator Agent
SYSTEM_PROMPT = """You are an Orchestrator Agent that coordinates multiple specialized agents to complete complex workflows.

Your responsibilities:
1. Parse user requests to extract key information (JIRA tickets, GitHub repos, request type)
2. Determine the correct sequence of agent calls based on request type
3. Coordinate workflow execution across multiple agents
4. Pass context between agents
5. Handle errors and provide clear status updates
6. Aggregate results into coherent responses

Available Specialized Agents:
- **JIRA Agent**: Fetch JIRA tickets, parse requirements, update ticket status
- **Planning Agent**: Generate implementation plans from requirements
- **GitHub Agent**: Manage GitHub issues, PRs, and comments
- **Coding Agent**: Execute code changes, run commands, and run tests in isolated workspaces

Request Types and Workflows:

1. **Implement** (feature implementation):
   - Fetch JIRA ticket requirements
   - Generate implementation plan
   - Create GitHub issue (if repo provided)
   - Execute implementation
   - Post results to GitHub (if repo provided)
   - Update JIRA ticket status

2. **Fix** (bug fixing):
   - Fetch JIRA bug details
   - Generate fix plan
   - Execute fix
   - Update JIRA status

3. **Test** (testing):
   - Run test suite
   - Post results to GitHub (if repo provided)

4. **Review** (code review):
   - Fetch JIRA review item
   - Generate review checklist

Guidelines:
- Always start by parsing the user request
- Determine the workflow based on request type and available information
- Execute agents in logical sequence
- Pass relevant context to each agent
- Provide clear status updates at each step
- Handle errors gracefully with informative messages
- Aggregate results into a coherent final response

Input Format:
Users will provide natural language requests like:
- "Based on JIRA-123, implement user authentication in myorg/myrepo"
- "Fix the bug in PROJ-456"
- "Run tests for the authentication module"

Your Process:
1. Parse the request to extract JIRA ticket, GitHub repo, and request type
2. Determine the appropriate workflow sequence
3. Execute the workflow (or describe the execution plan)
4. Provide a summary of results

Available Tools:
- parse_user_request(prompt): Extract JIRA ticket, GitHub repo, and request type
- determine_workflow(request_type, has_jira, has_repo): Determine workflow steps
- execute_workflow_sequence(workflow_type, jira_ticket, github_repo, user_id): Execute workflow

Best Practices:
- Always parse requests first to understand what's needed
- Validate that required information is present (JIRA ticket for implement/fix)
- Provide clear workflow descriptions
- Handle missing information gracefully
- Give users visibility into what will happen before execution
"""

# Create agent with orchestrator tools
agent = Agent(
    model=model,
    tools=[
        parse_user_request,
        determine_workflow,
        execute_workflow_sequence,
    ],
    system_prompt=SYSTEM_PROMPT,
)


@app.entrypoint
async def strands_agent_orchestrator(payload):
    """
    AgentCore Runtime entrypoint for Orchestrator Agent.

    Args:
        payload: Request payload with prompt and optional parameters

    Returns:
        Agent response with workflow coordination results
    """
    user_input = payload.get("prompt", "")
    print(f"📥 Orchestrator agent input: {user_input}")

    # Execute agent
    response = agent(user_input)

    print(f"📤 Orchestrator agent response: {response.message}")

    return {"result": response.message}
