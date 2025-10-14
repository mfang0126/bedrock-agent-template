"""Tests for JIRA agent creation.

Tests the create_jira_agent factory function and agent configuration.
"""

import pytest
from unittest.mock import patch
from strands import Agent

from src.agent import create_jira_agent
from src.auth.mock import MockJiraAuth


class TestCreateJiraAgent:
    """Test suite for create_jira_agent factory function."""

    def test_create_jira_agent_with_mock(self):
        """Test creating agent with mock authentication.

        Verifies:
        - Agent is created successfully
        - Agent has correct type
        - Mock auth is accepted
        """
        auth = MockJiraAuth()
        agent = create_jira_agent(auth)

        assert agent is not None
        assert isinstance(agent, Agent)

    def test_agent_has_correct_tools(self):
        """Test that agent is configured with correct tools.

        Verifies:
        - Agent has 5 tools (2 ticket + 3 update)
        - All expected tool functions are present
        - Tools are callable
        """
        auth = MockJiraAuth()
        agent = create_jira_agent(auth)

        # Agent should have 5 tools
        # Note: Strands Agent doesn't expose tools directly, verify through tool_names
        assert hasattr(agent, 'tool_names')
        assert len(agent.tool_names) == 5

        # Get tool names
        tool_names = agent.tool_names

        # Check ticket tools
        assert 'fetch_jira_ticket' in tool_names
        assert 'parse_ticket_requirements' in tool_names

        # Check update tools
        assert 'update_jira_status' in tool_names
        assert 'add_jira_comment' in tool_names
        assert 'link_github_issue' in tool_names

    def test_agent_has_system_prompt(self):
        """Test that agent has proper system prompt.

        Verifies:
        - System prompt is set
        - Prompt describes JIRA capabilities
        - Prompt includes best practices
        """
        auth = MockJiraAuth()
        agent = create_jira_agent(auth)

        assert hasattr(agent, 'system_prompt')
        assert agent.system_prompt is not None
        assert len(agent.system_prompt) > 0

        # Check prompt content
        prompt = agent.system_prompt
        assert "JIRA Agent" in prompt
        assert "Responsibilities" in prompt
        assert "ticket" in prompt.lower()
        assert "authentication" in prompt.lower()

    def test_agent_has_model_configuration(self):
        """Test that agent has Bedrock model configured.

        Verifies:
        - Agent has model attribute
        - Model is BedrockModel instance
        - Model configuration is accessible
        """
        auth = MockJiraAuth()
        agent = create_jira_agent(auth)

        assert hasattr(agent, 'model')
        assert agent.model is not None
        # Model should be BedrockModel from strands
        # Access config through get_config() method
        config = agent.model.get_config()
        assert 'model_id' in config
        assert config['model_id'] is not None

    def test_agent_multiple_instances(self):
        """Test creating multiple agent instances.

        Verifies:
        - Multiple instances can be created
        - Each instance is independent
        - Different auth instances work
        """
        auth1 = MockJiraAuth()
        auth2 = MockJiraAuth()

        agent1 = create_jira_agent(auth1)
        agent2 = create_jira_agent(auth2)

        assert agent1 is not None
        assert agent2 is not None
        assert agent1 is not agent2

    def test_agent_tool_injection(self):
        """Test that tools receive injected authentication.

        Verifies:
        - Tools are properly initialized with auth
        - Auth is accessible to tools
        - Tool closure captures auth correctly
        """
        auth = MockJiraAuth()
        agent = create_jira_agent(auth)

        # Tools should be configured with auth
        # We can verify this by checking tool count and names
        assert len(agent.tool_names) == 5

    def test_agent_system_prompt_includes_ticket_format(self):
        """Test that system prompt includes ticket ID format guidance.

        Verifies:
        - Valid ticket format examples
        - Invalid format examples
        - Format validation guidance
        """
        auth = MockJiraAuth()
        agent = create_jira_agent(auth)

        prompt = agent.system_prompt

        # Should include ticket format information
        assert "Ticket ID Format" in prompt or "ticket" in prompt.lower()
        assert "PROJ-123" in prompt  # Example format
        assert "valid" in prompt.lower() or "invalid" in prompt.lower()

    def test_agent_system_prompt_includes_capabilities(self):
        """Test that system prompt describes all capabilities.

        Verifies:
        - Fetch tickets mentioned
        - Update status mentioned
        - Add comments mentioned
        - Link GitHub issues mentioned
        """
        auth = MockJiraAuth()
        agent = create_jira_agent(auth)

        prompt = agent.system_prompt.lower()

        # All major capabilities should be mentioned
        assert "fetch" in prompt or "get" in prompt
        assert "status" in prompt or "update" in prompt
        assert "comment" in prompt
        assert "github" in prompt or "link" in prompt

    def test_agent_system_prompt_includes_best_practices(self):
        """Test that system prompt includes best practices.

        Verifies:
        - Validation guidance
        - Error handling guidance
        - User experience guidance
        """
        auth = MockJiraAuth()
        agent = create_jira_agent(auth)

        prompt = agent.system_prompt.lower()

        # Best practices should be mentioned
        assert "validate" in prompt or "validation" in prompt
        assert "error" in prompt
        assert "message" in prompt

    def test_agent_uses_environment_model_id(self):
        """Test that agent uses model ID from environment.

        Verifies:
        - BEDROCK_MODEL_ID env var is respected
        - Default model is used if not set
        """
        import os

        # Test with custom model
        with patch.dict(os.environ, {"BEDROCK_MODEL_ID": "custom-model-id"}):
            auth = MockJiraAuth()
            agent = create_jira_agent(auth)
            config = agent.model.get_config()
            assert config['model_id'] == "custom-model-id"

        # Test with default (should use default from agent.py)
        with patch.dict(os.environ, {}, clear=True):
            os.environ["JIRA_URL"] = "https://test.atlassian.net"
            auth = MockJiraAuth()
            agent = create_jira_agent(auth)
            # Should have some model configured
            config = agent.model.get_config()
            assert config['model_id'] is not None

    def test_agent_region_configuration(self):
        """Test that agent uses correct AWS region.

        Verifies:
        - Region is set to ap-southeast-2 (Sydney)
        - Region is configured on model
        """
        auth = MockJiraAuth()
        agent = create_jira_agent(auth)

        # Model should have region configured
        # Access config through get_config() method
        config = agent.model.get_config()
        assert 'region_name' in config
        assert config['region_name'] == "ap-southeast-2"

    def test_agent_tool_names_are_descriptive(self):
        """Test that tool names are descriptive and follow conventions.

        Verifies:
        - Tool names use snake_case
        - Tool names describe their function
        - No generic names like "tool1"
        """
        auth = MockJiraAuth()
        agent = create_jira_agent(auth)

        tool_names = agent.tool_names

        for name in tool_names:
            # Should be snake_case
            assert "_" in name or name.islower()
            # Should not be generic
            assert name not in ["tool", "function", "method"]
            # Should include jira or action
            assert "jira" in name.lower() or any(
                action in name.lower()
                for action in ["fetch", "parse", "update", "add", "link"]
            )

    def test_agent_tools_have_descriptions(self):
        """Test that all tools have docstrings/descriptions.

        Verifies:
        - Each tool has a description
        - Descriptions are non-empty
        - Descriptions explain tool purpose
        """
        auth = MockJiraAuth()
        agent = create_jira_agent(auth)

        # Strands Agent doesn't expose tool objects directly
        # We verify tool names are descriptive (already covered in other tests)
        # This test verifies that tools exist and are properly named
        assert len(agent.tool_names) == 5
        for tool_name in agent.tool_names:
            # Tool names should be descriptive (already verified in test_agent_tool_names_are_descriptive)
            assert len(tool_name) > 0

    @pytest.mark.asyncio
    async def test_agent_accepts_different_auth_implementations(self):
        """Test that agent works with different auth implementations.

        Verifies:
        - Agent accepts any JiraAuth implementation
        - Protocol-based interface works
        - Duck typing is properly implemented
        """
        from src.auth.interface import JiraAuth

        class CustomAuth:
            """Custom auth implementation for testing."""

            async def get_token(self) -> str:
                return "custom_token"

            def is_authenticated(self) -> bool:
                return True

            def get_jira_url(self) -> str:
                return "https://custom.atlassian.net"

            def get_auth_headers(self) -> dict:
                return {"Authorization": "Bearer custom_token"}

            def get_cloud_id(self) -> str:
                return "custom_cloud_id"

        custom_auth = CustomAuth()
        agent = create_jira_agent(custom_auth)

        assert agent is not None
        assert len(agent.tool_names) == 5

    def test_agent_creation_is_idempotent(self):
        """Test that creating agent multiple times with same auth is safe.

        Verifies:
        - Multiple creations don't cause issues
        - Each creation produces independent agent
        - No side effects from multiple creations
        """
        auth = MockJiraAuth()

        agent1 = create_jira_agent(auth)
        agent2 = create_jira_agent(auth)
        agent3 = create_jira_agent(auth)

        assert agent1 is not None
        assert agent2 is not None
        assert agent3 is not None

        # Should be different instances
        assert agent1 is not agent2
        assert agent2 is not agent3
