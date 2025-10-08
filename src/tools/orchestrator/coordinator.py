"""
Agent coordination tools for Orchestrator Agent.

Executes workflows by coordinating multiple agents.
"""

import json
import os
from typing import Dict, List, Optional
from strands.tools import tool


# Agent ARN mappings (loaded from environment or config)
AGENT_ARNS = {
    "jira": os.getenv("JIRA_AGENT_ARN", ""),
    "planning": os.getenv("PLANNING_AGENT_ARN", ""),
    "github": os.getenv("GITHUB_AGENT_ARN", ""),
    "coding": os.getenv("CODING_AGENT_ARN", ""),
}


@tool
async def determine_workflow(request_type: str, has_jira: bool = False, has_repo: bool = False) -> str:
    """
    Determine the workflow sequence based on request type and available information.

    Args:
        request_type: Type of request (implement|fix|test|review)
        has_jira: Whether JIRA ticket ID is provided
        has_repo: Whether GitHub repo is provided

    Returns:
        Workflow description
    """
    try:
        workflow = []

        if request_type == "implement":
            if has_jira:
                workflow = [
                    "1. JIRA Agent: Fetch ticket requirements",
                    "2. Planning Agent: Generate implementation plan",
                    "3. Coding Agent: Execute the plan",
                    "4. JIRA Agent: Update ticket status"
                ]
                if has_repo:
                    workflow.insert(2, "2.5. GitHub Agent: Create GitHub issue")
                    workflow.insert(4, "3.5. GitHub Agent: Post implementation results")

        elif request_type == "fix":
            if has_jira:
                workflow = [
                    "1. JIRA Agent: Fetch bug details",
                    "2. Planning Agent: Generate fix plan",
                    "3. Coding Agent: Execute fix",
                    "4. JIRA Agent: Update bug status"
                ]

        elif request_type == "test":
            workflow = [
                "1. Coding Agent: Run test suite",
                "2. Report results"
            ]
            if has_repo:
                workflow.insert(1, "1.5. GitHub Agent: Post test results")

        elif request_type == "review":
            if has_jira:
                workflow = [
                    "1. JIRA Agent: Fetch item for review",
                    "2. Planning Agent: Generate review checklist"
                ]

        if not workflow:
            return f"""❌ Cannot determine workflow

Request Type: {request_type}
Has JIRA: {has_jira}
Has Repo: {has_repo}

Please provide more information or use a different request type."""

        workflow_text = "\n".join(workflow)
        return f"""✅ Workflow determined

Request Type: {request_type}

Workflow Steps:
{workflow_text}"""

    except Exception as e:
        return f"❌ Error determining workflow: {str(e)}"


@tool
async def execute_workflow_sequence(
    workflow_type: str,
    jira_ticket: Optional[str] = None,
    github_repo: Optional[str] = None,
    user_id: str = "test"
) -> str:
    """
    Execute a workflow sequence by calling agents in order.

    This is a simplified implementation that describes the workflow.
    Full implementation would use boto3 to call actual AgentCore agents.

    Args:
        workflow_type: Type of workflow (implement|fix|test|review)
        jira_ticket: Optional JIRA ticket ID
        github_repo: Optional GitHub repository
        user_id: User ID for agent invocations

    Returns:
        Workflow execution summary
    """
    try:
        results = []
        context = {
            "jira_ticket": jira_ticket,
            "github_repo": github_repo,
            "user_id": user_id
        }

        # Simplified workflow execution (demonstration)
        # In production, this would use boto3 bedrock-agent-runtime to invoke agents

        if workflow_type == "implement" and jira_ticket:
            results.append(f"""Step 1: JIRA Agent
- Action: Fetch ticket {jira_ticket}
- Status: Ready to execute
- Next: Pass requirements to Planning Agent""")

            results.append(f"""Step 2: Planning Agent
- Action: Generate implementation plan
- Input: Requirements from JIRA ticket {jira_ticket}
- Status: Ready to execute
- Next: Pass plan to Coding Agent""")

            results.append(f"""Step 3: Coding Agent
- Action: Execute implementation plan
- Input: Plan from Planning Agent
- Status: Ready to execute
- Next: Update JIRA ticket""")

            if github_repo:
                results.append(f"""Step 3.5: GitHub Agent
- Action: Create issue and post results
- Repo: {github_repo}
- Status: Ready to execute""")

            results.append(f"""Step 4: JIRA Agent
- Action: Update ticket {jira_ticket} status
- Status: Ready to execute
- Next: Final report""")

        elif workflow_type == "test":
            results.append(f"""Step 1: Coding Agent
- Action: Run test suite
- Repo: {github_repo or 'current workspace'}
- Status: Ready to execute
- Next: Report results""")

        else:
            return f"❌ Unsupported workflow type: {workflow_type}"

        summary = "\n\n".join(results)
        return f"""✅ Workflow Sequence Ready

Workflow Type: {workflow_type}
JIRA Ticket: {jira_ticket or 'N/A'}
GitHub Repo: {github_repo or 'N/A'}

{summary}

📝 Note: This is a workflow plan. To execute, each agent would be invoked via AgentCore with proper context passing."""

    except Exception as e:
        return f"❌ Error executing workflow: {str(e)}"


def get_agent_arn(agent_name: str) -> Optional[str]:
    """Get agent ARN from configuration."""
    arn = AGENT_ARNS.get(agent_name)
    if not arn:
        raise ValueError(f"ARN not configured for agent: {agent_name}")
    return arn
