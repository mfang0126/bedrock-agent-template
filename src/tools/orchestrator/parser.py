"""
Request parsing tools for Orchestrator Agent.

Extracts key information from user requests to determine workflow.
"""

import re
from typing import Dict
from strands.tools import tool


@tool
async def parse_user_request(prompt: str) -> str:
    """
    Parse user request to extract JIRA ticket, GitHub repo, and request type.

    Args:
        prompt: User's natural language request

    Returns:
        JSON string with parsed information
    """
    try:
        parsed = {
            "jira_ticket": None,
            "github_repo": None,
            "request_type": "implement",  # implement|fix|test|review
            "raw_input": prompt
        }

        # Extract JIRA ticket ID (format: PROJECT-123)
        jira_match = re.search(r'([A-Z]{2,10}-\d+)', prompt, re.IGNORECASE)
        if jira_match:
            parsed["jira_ticket"] = jira_match.group(1).upper()

        # Extract GitHub repo (format: owner/repo)
        repo_match = re.search(r'([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)', prompt)
        if repo_match:
            parsed["github_repo"] = repo_match.group(1)

        # Determine request type from keywords
        prompt_lower = prompt.lower()
        if any(word in prompt_lower for word in ["fix", "bug", "issue", "error"]):
            parsed["request_type"] = "fix"
        elif any(word in prompt_lower for word in ["test", "testing", "validate"]):
            parsed["request_type"] = "test"
        elif any(word in prompt_lower for word in ["review", "check", "audit"]):
            parsed["request_type"] = "review"
        elif any(word in prompt_lower for word in ["implement", "add", "create", "build", "feature"]):
            parsed["request_type"] = "implement"

        # Format response
        response = f"""✅ Request parsed successfully

JIRA Ticket: {parsed['jira_ticket'] or 'Not specified'}
GitHub Repo: {parsed['github_repo'] or 'Not specified'}
Request Type: {parsed['request_type']}

Raw Input: {prompt}"""

        return response

    except Exception as e:
        return f"❌ Error parsing request: {str(e)}"


def extract_jira_ticket(prompt: str) -> str:
    """Extract JIRA ticket ID from prompt."""
    match = re.search(r'([A-Z]{2,10}-\d+)', prompt, re.IGNORECASE)
    return match.group(1).upper() if match else None


def extract_github_repo(prompt: str) -> str:
    """Extract GitHub repository from prompt."""
    match = re.search(r'([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)', prompt)
    return match.group(1) if match else None


def determine_request_type(prompt: str) -> str:
    """Determine request type from prompt keywords."""
    prompt_lower = prompt.lower()

    if any(word in prompt_lower for word in ["fix", "bug", "issue", "error"]):
        return "fix"
    elif any(word in prompt_lower for word in ["test", "testing", "validate"]):
        return "test"
    elif any(word in prompt_lower for word in ["review", "check", "audit"]):
        return "review"
    else:
        return "implement"
