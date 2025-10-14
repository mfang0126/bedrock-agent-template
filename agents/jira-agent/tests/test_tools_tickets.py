"""Tests for JIRA ticket tools.

Tests the JiraTicketTools class for fetching and parsing tickets.
"""

import pytest
from pytest_httpx import HTTPXMock
from src.tools.tickets import JiraTicketTools


class TestFetchJiraTicket:
    """Test suite for fetch_jira_ticket tool."""

    @pytest.mark.asyncio
    async def test_fetch_jira_ticket_valid_format(
        self, ticket_tools: JiraTicketTools, mock_ticket_response: dict, httpx_mock: HTTPXMock
    ):
        """Test fetching ticket with valid ID format.

        Verifies:
        - Valid ticket ID is accepted
        - API call is made with correct URL
        - Response is properly parsed
        - Success response structure
        """
        ticket_id = "PROJ-123"
        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}",
            json=mock_ticket_response,
            status_code=200
        )

        result = await ticket_tools.fetch_jira_ticket(ticket_id)

        assert result["success"] is True
        assert result["data"]["ticket_id"] == ticket_id
        assert result["data"]["title"] == "Implement user authentication"
        assert result["data"]["status"] == "In Progress"
        assert result["message"] == f"Successfully fetched ticket {ticket_id}"

    @pytest.mark.asyncio
    async def test_fetch_jira_ticket_invalid_format_lowercase(self, ticket_tools: JiraTicketTools):
        """Test fetching ticket with lowercase project key.

        Verifies:
        - Invalid format (lowercase) is rejected
        - Error message indicates format issue
        - No API call is made
        """
        result = await ticket_tools.fetch_jira_ticket("proj-123")

        assert result["success"] is False
        assert "Invalid ticket ID format" in result["message"]
        assert result["data"] == {}

    @pytest.mark.asyncio
    async def test_fetch_jira_ticket_invalid_format_missing_number(self, ticket_tools: JiraTicketTools):
        """Test fetching ticket without number.

        Verifies:
        - Format without number is rejected
        - Proper error message
        """
        result = await ticket_tools.fetch_jira_ticket("PROJ-")

        assert result["success"] is False
        assert "Invalid ticket ID format" in result["message"]

    @pytest.mark.asyncio
    async def test_fetch_jira_ticket_invalid_format_too_long_project(self, ticket_tools: JiraTicketTools):
        """Test fetching ticket with excessively long project key.

        Verifies:
        - Project keys longer than 10 chars are rejected
        - Validation catches edge cases
        """
        result = await ticket_tools.fetch_jira_ticket("TOOLONGPROJECT-123")

        assert result["success"] is False
        assert "Invalid ticket ID format" in result["message"]

    @pytest.mark.asyncio
    async def test_fetch_jira_ticket_invalid_format_too_short_project(self, ticket_tools: JiraTicketTools):
        """Test fetching ticket with too short project key.

        Verifies:
        - Project keys shorter than 2 chars are rejected
        """
        result = await ticket_tools.fetch_jira_ticket("P-123")

        assert result["success"] is False
        assert "Invalid ticket ID format" in result["message"]

    @pytest.mark.asyncio
    async def test_fetch_jira_ticket_empty_id(self, ticket_tools: JiraTicketTools):
        """Test fetching ticket with empty ID.

        Verifies:
        - Empty string is rejected
        - Proper validation
        """
        result = await ticket_tools.fetch_jira_ticket("")

        assert result["success"] is False
        assert "Invalid ticket ID format" in result["message"]

    @pytest.mark.asyncio
    async def test_fetch_jira_ticket_not_found(
        self, ticket_tools: JiraTicketTools, httpx_mock: HTTPXMock
    ):
        """Test fetching non-existent ticket.

        Verifies:
        - 404 status is handled
        - Error message indicates ticket not found
        - Proper error response structure
        """
        ticket_id = "PROJ-999"
        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}",
            status_code=404
        )

        result = await ticket_tools.fetch_jira_ticket(ticket_id)

        assert result["success"] is False
        assert "not found" in result["message"].lower()
        assert result["data"] == {}

    @pytest.mark.asyncio
    async def test_fetch_jira_ticket_authentication_error(
        self, ticket_tools: JiraTicketTools, httpx_mock: HTTPXMock
    ):
        """Test fetching ticket with authentication failure.

        Verifies:
        - 401 status is handled
        - Error message indicates auth failure
        """
        ticket_id = "PROJ-123"
        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}",
            status_code=401
        )

        result = await ticket_tools.fetch_jira_ticket(ticket_id)

        assert result["success"] is False
        assert "authentication failed" in result["message"].lower()
        assert "credentials" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_fetch_jira_ticket_server_error(
        self, ticket_tools: JiraTicketTools, httpx_mock: HTTPXMock
    ):
        """Test fetching ticket with server error.

        Verifies:
        - 500 status is handled
        - Error message includes status code
        """
        ticket_id = "PROJ-123"
        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}",
            status_code=500,
            text="Internal Server Error"
        )

        result = await ticket_tools.fetch_jira_ticket(ticket_id)

        assert result["success"] is False
        assert "500" in result["message"]
        assert "error" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_fetch_jira_ticket_timeout(
        self, ticket_tools: JiraTicketTools, httpx_mock: HTTPXMock
    ):
        """Test fetching ticket with timeout.

        Verifies:
        - Timeout exception is caught
        - User-friendly error message
        """
        from httpx import TimeoutException

        ticket_id = "PROJ-123"
        httpx_mock.add_exception(
            TimeoutException("Request timed out"),
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}"
        )

        result = await ticket_tools.fetch_jira_ticket(ticket_id)

        assert result["success"] is False
        assert "timed out" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_fetch_jira_ticket_data_structure(
        self, ticket_tools: JiraTicketTools, mock_ticket_response: dict, httpx_mock: HTTPXMock
    ):
        """Test that fetched ticket data has correct structure.

        Verifies:
        - All expected fields are present
        - Field types are correct
        - Formatted output is included
        """
        ticket_id = "PROJ-123"
        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}",
            json=mock_ticket_response,
            status_code=200
        )

        result = await ticket_tools.fetch_jira_ticket(ticket_id)

        assert result["success"] is True
        data = result["data"]

        # Check required fields
        assert "ticket_id" in data
        assert "title" in data
        assert "description" in data
        assert "status" in data
        assert "priority" in data
        assert "assignee" in data
        assert "labels" in data
        assert "formatted_output" in data

        # Check types
        assert isinstance(data["labels"], list)
        assert isinstance(data["formatted_output"], str)

    @pytest.mark.asyncio
    async def test_fetch_jira_ticket_acceptance_criteria_extraction(
        self, ticket_tools: JiraTicketTools, mock_ticket_response: dict, httpx_mock: HTTPXMock
    ):
        """Test extraction of acceptance criteria from description.

        Verifies:
        - Acceptance criteria are parsed
        - Bullet points are extracted
        - Criteria list is properly structured
        """
        ticket_id = "PROJ-123"
        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}",
            json=mock_ticket_response,
            status_code=200
        )

        result = await ticket_tools.fetch_jira_ticket(ticket_id)

        assert result["success"] is True
        criteria = result["data"]["acceptance_criteria"]

        assert isinstance(criteria, list)
        assert len(criteria) > 0
        assert "Users can log in" in criteria
        assert "Tokens expire after 1 hour" in criteria

    @pytest.mark.asyncio
    async def test_fetch_jira_ticket_no_acceptance_criteria(
        self, ticket_tools: JiraTicketTools, httpx_mock: HTTPXMock
    ):
        """Test ticket without acceptance criteria.

        Verifies:
        - Missing criteria is handled gracefully
        - Empty list is returned
        """
        ticket_response = {
            "key": "PROJ-456",
            "fields": {
                "summary": "Simple task",
                "description": "Just a simple description without criteria",
                "status": {"name": "To Do"},
                "priority": {"name": "Low"},
                "assignee": None,
                "labels": []
            }
        }

        httpx_mock.add_response(
            url="https://test.atlassian.net/rest/api/3/issue/PROJ-456",
            json=ticket_response,
            status_code=200
        )

        result = await ticket_tools.fetch_jira_ticket("PROJ-456")

        assert result["success"] is True
        assert result["data"]["acceptance_criteria"] == []

    @pytest.mark.asyncio
    async def test_fetch_jira_ticket_unassigned(
        self, ticket_tools: JiraTicketTools, httpx_mock: HTTPXMock
    ):
        """Test ticket without assignee.

        Verifies:
        - Null assignee is handled
        - "Unassigned" text is shown
        """
        ticket_response = {
            "key": "PROJ-789",
            "fields": {
                "summary": "Unassigned ticket",
                "description": "Description",
                "status": {"name": "To Do"},
                "priority": {"name": "Medium"},
                "assignee": None,
                "labels": []
            }
        }

        httpx_mock.add_response(
            url="https://test.atlassian.net/rest/api/3/issue/PROJ-789",
            json=ticket_response,
            status_code=200
        )

        result = await ticket_tools.fetch_jira_ticket("PROJ-789")

        assert result["success"] is True
        assert result["data"]["assignee"] == "Unassigned"


class TestParseTicketRequirements:
    """Test suite for parse_ticket_requirements tool."""

    @pytest.mark.asyncio
    async def test_parse_ticket_requirements_success(
        self, ticket_tools: JiraTicketTools, mock_ticket_response: dict, httpx_mock: HTTPXMock
    ):
        """Test parsing requirements from valid ticket.

        Verifies:
        - Ticket is fetched successfully
        - Requirements are extracted
        - Formatted requirements text is generated
        """
        ticket_id = "PROJ-123"
        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}",
            json=mock_ticket_response,
            status_code=200
        )

        result = await ticket_tools.parse_ticket_requirements(ticket_id)

        assert result["success"] is True
        assert result["data"]["ticket_id"] == ticket_id
        assert "requirements" in result["data"]
        assert "formatted_requirements" in result["data"]
        assert "Requirements from" in result["data"]["formatted_requirements"]

    @pytest.mark.asyncio
    async def test_parse_ticket_requirements_invalid_ticket(
        self, ticket_tools: JiraTicketTools
    ):
        """Test parsing requirements from invalid ticket ID.

        Verifies:
        - Invalid ID validation is applied
        - Error is propagated from fetch_jira_ticket
        """
        result = await ticket_tools.parse_ticket_requirements("invalid")

        assert result["success"] is False
        assert "Invalid ticket ID format" in result["message"]

    @pytest.mark.asyncio
    async def test_parse_ticket_requirements_not_found(
        self, ticket_tools: JiraTicketTools, httpx_mock: HTTPXMock
    ):
        """Test parsing requirements from non-existent ticket.

        Verifies:
        - Fetch failure is propagated
        - Error response structure is maintained
        """
        ticket_id = "PROJ-999"
        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}",
            status_code=404
        )

        result = await ticket_tools.parse_ticket_requirements(ticket_id)

        assert result["success"] is False
        assert "not found" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_parse_ticket_requirements_structure(
        self, ticket_tools: JiraTicketTools, mock_ticket_response: dict, httpx_mock: HTTPXMock
    ):
        """Test requirements data structure.

        Verifies:
        - Requirements include all ticket data
        - Formatted text is properly structured
        - Planning Agent note is included
        """
        ticket_id = "PROJ-123"
        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}",
            json=mock_ticket_response,
            status_code=200
        )

        result = await ticket_tools.parse_ticket_requirements(ticket_id)

        assert result["success"] is True
        formatted = result["data"]["formatted_requirements"]

        assert "Requirements from PROJ-123" in formatted
        assert "Planning Agent" in formatted
        assert result["data"]["requirements"]["title"] == "Implement user authentication"
