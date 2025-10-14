"""Pytest configuration and shared fixtures for JIRA Agent tests."""

import os
import pytest
from typing import AsyncGenerator
import httpx

from src.auth.mock import MockJiraAuth
from src.auth.interface import JiraAuth
from src.tools.tickets import JiraTicketTools
from src.tools.updates import JiraUpdateTools


@pytest.fixture
def mock_auth() -> MockJiraAuth:
    """Provide mock JIRA authentication.

    Returns:
        MockJiraAuth instance for testing
    """
    # Set test environment
    os.environ["JIRA_URL"] = "https://test.atlassian.net"
    return MockJiraAuth()


@pytest.fixture
def ticket_tools(mock_auth: JiraAuth) -> JiraTicketTools:
    """Provide JIRA ticket tools with mock auth.

    Args:
        mock_auth: Mock authentication fixture

    Returns:
        JiraTicketTools instance for testing
    """
    return JiraTicketTools(auth=mock_auth)


@pytest.fixture
def update_tools(mock_auth: JiraAuth) -> JiraUpdateTools:
    """Provide JIRA update tools with mock auth.

    Args:
        mock_auth: Mock authentication fixture

    Returns:
        JiraUpdateTools instance for testing
    """
    return JiraUpdateTools(auth=mock_auth)


@pytest.fixture
async def mock_httpx_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide async HTTP client for testing.

    Yields:
        Async HTTP client instance
    """
    async with httpx.AsyncClient() as client:
        yield client


# Mock response data fixtures

@pytest.fixture
def mock_ticket_response() -> dict:
    """Provide mock JIRA ticket API response.

    Returns:
        Mock ticket data matching JIRA API format
    """
    return {
        "id": "10001",
        "key": "PROJ-123",
        "fields": {
            "summary": "Implement user authentication",
            "description": "Add JWT-based authentication\n\nAcceptance Criteria:\n- Users can log in\n- Tokens expire after 1 hour\n- Refresh tokens work",
            "status": {"name": "In Progress"},
            "priority": {"name": "High"},
            "assignee": {"displayName": "John Doe"},
            "labels": ["auth", "security"],
        }
    }


@pytest.fixture
def mock_transitions_response() -> dict:
    """Provide mock JIRA transitions API response.

    Returns:
        Mock transitions data matching JIRA API format
    """
    return {
        "transitions": [
            {"id": "11", "name": "To Do"},
            {"id": "21", "name": "In Progress"},
            {"id": "31", "name": "Done"},
            {"id": "41", "name": "Blocked"},
        ]
    }


@pytest.fixture
def mock_comment_response() -> dict:
    """Provide mock JIRA comment API response.

    Returns:
        Mock comment data matching JIRA API format
    """
    return {
        "id": "10050",
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Work started on this ticket"}
                    ]
                }
            ]
        },
        "created": "2024-10-15T12:00:00.000+0000",
        "author": {"displayName": "Test User"}
    }


@pytest.fixture
def mock_remotelink_response() -> dict:
    """Provide mock JIRA remote link API response.

    Returns:
        Mock remote link data matching JIRA API format
    """
    return {
        "id": 10000,
        "self": "https://test.atlassian.net/rest/api/3/issue/PROJ-123/remotelink/10000"
    }


# Environment setup fixtures

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables.

    Automatically used for all tests to ensure clean environment.
    """
    original_env = os.environ.copy()

    # Set test environment
    os.environ["JIRA_URL"] = "https://test.atlassian.net"
    os.environ["BEDROCK_MODEL_ID"] = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
