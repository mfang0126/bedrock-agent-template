"""Tests for JIRA update tools.

Tests the JiraUpdateTools class for status updates, comments, and linking.
"""

import pytest
from pytest_httpx import HTTPXMock
from src.tools.updates import JiraUpdateTools


class TestUpdateJiraStatus:
    """Test suite for update_jira_status tool."""

    @pytest.mark.asyncio
    async def test_update_jira_status_success(
        self, update_tools: JiraUpdateTools, mock_transitions_response: dict, httpx_mock: HTTPXMock
    ):
        """Test successful status update.

        Verifies:
        - Valid transition is found and executed
        - API calls are made correctly
        - Success response structure
        """
        ticket_id = "PROJ-123"
        new_status = "Done"

        # Mock transitions fetch
        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}/transitions",
            json=mock_transitions_response,
            status_code=200,
            method="GET"
        )

        # Mock transition execution
        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}/transitions",
            status_code=204,
            method="POST"
        )

        result = await update_tools.update_jira_status(ticket_id, new_status)

        assert result["success"] is True
        assert result["data"]["ticket_id"] == ticket_id
        assert result["data"]["new_status"] == "Done"
        assert "moved to" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_update_jira_status_case_insensitive(
        self, update_tools: JiraUpdateTools, mock_transitions_response: dict, httpx_mock: HTTPXMock
    ):
        """Test status update with case-insensitive matching.

        Verifies:
        - Status name matching is case-insensitive
        - "in progress" matches "In Progress"
        """
        ticket_id = "PROJ-123"

        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}/transitions",
            json=mock_transitions_response,
            status_code=200,
            method="GET"
        )

        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}/transitions",
            status_code=204,
            method="POST"
        )

        result = await update_tools.update_jira_status(ticket_id, "in progress")

        assert result["success"] is True
        assert result["data"]["new_status"] == "In Progress"

    @pytest.mark.asyncio
    async def test_update_jira_status_invalid_transition(
        self, update_tools: JiraUpdateTools, mock_transitions_response: dict, httpx_mock: HTTPXMock
    ):
        """Test status update with invalid transition.

        Verifies:
        - Invalid transition is rejected
        - Available transitions are shown in error
        - Error response includes suggestions
        """
        ticket_id = "PROJ-123"

        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}/transitions",
            json=mock_transitions_response,
            status_code=200
        )

        result = await update_tools.update_jira_status(ticket_id, "Invalid Status")

        assert result["success"] is False
        assert "cannot transition" in result["message"].lower()
        assert "available transitions" in result["message"].lower()
        assert "available_transitions" in result["data"]
        assert len(result["data"]["available_transitions"]) > 0

    @pytest.mark.asyncio
    async def test_update_jira_status_invalid_ticket_id(self, update_tools: JiraUpdateTools):
        """Test status update with invalid ticket ID.

        Verifies:
        - Invalid ticket ID is rejected
        - No API calls are made
        """
        result = await update_tools.update_jira_status("invalid", "Done")

        assert result["success"] is False
        assert "invalid ticket id format" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_update_jira_status_empty_status(self, update_tools: JiraUpdateTools):
        """Test status update with empty status.

        Verifies:
        - Empty status is rejected
        - Proper validation message
        """
        result = await update_tools.update_jira_status("PROJ-123", "")

        assert result["success"] is False
        assert "status cannot be empty" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_update_jira_status_fetch_transitions_error(
        self, update_tools: JiraUpdateTools, httpx_mock: HTTPXMock
    ):
        """Test status update when fetching transitions fails.

        Verifies:
        - Error fetching transitions is handled
        - Error message is descriptive
        """
        ticket_id = "PROJ-123"

        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}/transitions",
            status_code=500
        )

        result = await update_tools.update_jira_status(ticket_id, "Done")

        assert result["success"] is False
        assert "error fetching transitions" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_update_jira_status_execution_error(
        self, update_tools: JiraUpdateTools, mock_transitions_response: dict, httpx_mock: HTTPXMock
    ):
        """Test status update when transition execution fails.

        Verifies:
        - Execution error is handled
        - Error message includes status code
        """
        ticket_id = "PROJ-123"

        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}/transitions",
            json=mock_transitions_response,
            status_code=200,
            method="GET"
        )

        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}/transitions",
            status_code=400,
            text="Bad Request",
            method="POST"
        )

        result = await update_tools.update_jira_status(ticket_id, "Done")

        assert result["success"] is False
        assert "error updating status" in result["message"].lower()
        assert "400" in result["message"]

    @pytest.mark.asyncio
    async def test_update_jira_status_timeout(
        self, update_tools: JiraUpdateTools, httpx_mock: HTTPXMock
    ):
        """Test status update with timeout.

        Verifies:
        - Timeout is handled gracefully
        - User-friendly error message
        """
        from httpx import TimeoutException

        ticket_id = "PROJ-123"

        httpx_mock.add_exception(
            TimeoutException("Request timed out"),
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}/transitions"
        )

        result = await update_tools.update_jira_status(ticket_id, "Done")

        assert result["success"] is False
        assert "timed out" in result["message"].lower()


class TestAddJiraComment:
    """Test suite for add_jira_comment tool."""

    @pytest.mark.asyncio
    async def test_add_jira_comment_success(
        self, update_tools: JiraUpdateTools, mock_comment_response: dict, httpx_mock: HTTPXMock
    ):
        """Test successful comment addition.

        Verifies:
        - Comment is added successfully
        - API request format is correct (ADF)
        - Success response structure
        """
        ticket_id = "PROJ-123"
        comment = "Work started on this ticket"

        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}/comment",
            json=mock_comment_response,
            status_code=201
        )

        result = await update_tools.add_jira_comment(ticket_id, comment)

        assert result["success"] is True
        assert result["data"]["ticket_id"] == ticket_id
        assert result["data"]["comment"] == comment
        assert "comment added" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_add_jira_comment_with_github_url(
        self, update_tools: JiraUpdateTools, mock_comment_response: dict, httpx_mock: HTTPXMock
    ):
        """Test adding comment with GitHub URL.

        Verifies:
        - GitHub URL is included in comment
        - URL is properly formatted
        - Success response includes URL
        """
        ticket_id = "PROJ-123"
        comment = "Fixed in PR"
        github_url = "https://github.com/org/repo/pull/456"

        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}/comment",
            json=mock_comment_response,
            status_code=201
        )

        result = await update_tools.add_jira_comment(ticket_id, comment, github_url)

        assert result["success"] is True
        assert result["data"]["github_url"] == github_url
        assert result["data"]["comment"] == comment

        # Verify request includes GitHub URL in body
        request = httpx_mock.get_request()
        assert request is not None
        import json
        body = json.loads(request.content)
        comment_text = body["body"]["content"][0]["content"][0]["text"]
        assert github_url in comment_text

    @pytest.mark.asyncio
    async def test_add_jira_comment_invalid_ticket_id(self, update_tools: JiraUpdateTools):
        """Test adding comment with invalid ticket ID.

        Verifies:
        - Invalid ticket ID is rejected
        - No API calls are made
        """
        result = await update_tools.add_jira_comment("invalid", "Comment")

        assert result["success"] is False
        assert "invalid ticket id format" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_add_jira_comment_empty_comment(self, update_tools: JiraUpdateTools):
        """Test adding empty comment.

        Verifies:
        - Empty comment is rejected
        - Validation error message
        """
        result = await update_tools.add_jira_comment("PROJ-123", "")

        assert result["success"] is False
        assert "comment cannot be empty" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_add_jira_comment_api_error(
        self, update_tools: JiraUpdateTools, httpx_mock: HTTPXMock
    ):
        """Test adding comment with API error.

        Verifies:
        - API error is handled
        - Error message includes status code
        """
        ticket_id = "PROJ-123"

        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}/comment",
            status_code=400,
            text="Bad Request"
        )

        result = await update_tools.add_jira_comment(ticket_id, "Comment")

        assert result["success"] is False
        assert "error adding comment" in result["message"].lower()
        assert "400" in result["message"]

    @pytest.mark.asyncio
    async def test_add_jira_comment_adf_format(
        self, update_tools: JiraUpdateTools, mock_comment_response: dict, httpx_mock: HTTPXMock
    ):
        """Test comment uses Atlassian Document Format (ADF).

        Verifies:
        - Request body uses ADF structure
        - Proper document structure with paragraphs
        - Text content is wrapped correctly
        """
        ticket_id = "PROJ-123"
        comment = "Test comment"

        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}/comment",
            json=mock_comment_response,
            status_code=201
        )

        await update_tools.add_jira_comment(ticket_id, comment)

        request = httpx_mock.get_request()
        assert request is not None
        import json
        body = json.loads(request.content)

        # Verify ADF structure
        assert body["body"]["type"] == "doc"
        assert body["body"]["version"] == 1
        assert "content" in body["body"]
        assert body["body"]["content"][0]["type"] == "paragraph"


class TestLinkGithubIssue:
    """Test suite for link_github_issue tool."""

    @pytest.mark.asyncio
    async def test_link_github_issue_success(
        self, update_tools: JiraUpdateTools, mock_remotelink_response: dict, httpx_mock: HTTPXMock
    ):
        """Test successful GitHub issue linking.

        Verifies:
        - Remote link is created successfully
        - API request includes proper URL and title
        - Success response structure
        """
        ticket_id = "PROJ-123"
        github_url = "https://github.com/org/repo/issues/123"

        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}/remotelink",
            json=mock_remotelink_response,
            status_code=201
        )

        result = await update_tools.link_github_issue(ticket_id, github_url)

        assert result["success"] is True
        assert result["data"]["ticket_id"] == ticket_id
        assert result["data"]["github_url"] == github_url
        assert result["data"]["link_type"] == "GitHub Issue"
        assert "linked github" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_link_github_pull_request(
        self, update_tools: JiraUpdateTools, mock_remotelink_response: dict, httpx_mock: HTTPXMock
    ):
        """Test linking GitHub pull request.

        Verifies:
        - PR URL is detected correctly
        - Link type is "GitHub Pull Request"
        - Different title for PRs vs issues
        """
        ticket_id = "PROJ-123"
        github_url = "https://github.com/org/repo/pull/456"

        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}/remotelink",
            json=mock_remotelink_response,
            status_code=201
        )

        result = await update_tools.link_github_issue(ticket_id, github_url)

        assert result["success"] is True
        assert result["data"]["link_type"] == "GitHub Pull Request"

    @pytest.mark.asyncio
    async def test_link_github_issue_invalid_ticket_id(self, update_tools: JiraUpdateTools):
        """Test linking with invalid ticket ID.

        Verifies:
        - Invalid ticket ID is rejected
        - No API calls are made
        """
        result = await update_tools.link_github_issue(
            "invalid",
            "https://github.com/org/repo/issues/123"
        )

        assert result["success"] is False
        assert "invalid ticket id format" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_link_github_issue_invalid_url(self, update_tools: JiraUpdateTools):
        """Test linking with invalid GitHub URL.

        Verifies:
        - Non-GitHub URLs are rejected
        - Validation error message
        """
        result = await update_tools.link_github_issue(
            "PROJ-123",
            "https://example.com/issue/123"
        )

        assert result["success"] is False
        assert "invalid github url" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_link_github_issue_empty_url(self, update_tools: JiraUpdateTools):
        """Test linking with empty URL.

        Verifies:
        - Empty URL is rejected
        - Proper validation
        """
        result = await update_tools.link_github_issue("PROJ-123", "")

        assert result["success"] is False
        assert "invalid github url" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_link_github_issue_api_error(
        self, update_tools: JiraUpdateTools, httpx_mock: HTTPXMock
    ):
        """Test linking with API error.

        Verifies:
        - API error is handled
        - Error message includes status code
        """
        ticket_id = "PROJ-123"
        github_url = "https://github.com/org/repo/issues/123"

        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}/remotelink",
            status_code=400,
            text="Bad Request"
        )

        result = await update_tools.link_github_issue(ticket_id, github_url)

        assert result["success"] is False
        assert "error linking" in result["message"].lower()
        assert "400" in result["message"]

    @pytest.mark.asyncio
    async def test_link_github_issue_request_format(
        self, update_tools: JiraUpdateTools, mock_remotelink_response: dict, httpx_mock: HTTPXMock
    ):
        """Test remote link request format.

        Verifies:
        - Request includes object with URL and title
        - GitHub icon is included
        - Proper JSON structure
        """
        ticket_id = "PROJ-123"
        github_url = "https://github.com/org/repo/issues/123"

        httpx_mock.add_response(
            url=f"https://test.atlassian.net/rest/api/3/issue/{ticket_id}/remotelink",
            json=mock_remotelink_response,
            status_code=201
        )

        await update_tools.link_github_issue(ticket_id, github_url)

        request = httpx_mock.get_request()
        assert request is not None
        import json
        body = json.loads(request.content)

        # Verify remote link structure
        assert "object" in body
        assert body["object"]["url"] == github_url
        assert "title" in body["object"]
        assert "icon" in body["object"]
        assert "favicon.ico" in body["object"]["icon"]["url16x16"]
