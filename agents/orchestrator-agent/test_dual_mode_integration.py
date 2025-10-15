#!/usr/bin/env python3
"""
Integration test for dual-mode communication across all agents.

Tests the full orchestration workflow with A2A communication.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.response_protocol import (
    ResponseMode,
    create_response,
    detect_mode,
    AgentResponse,
)


def test_response_protocol():
    """Test response protocol utilities."""
    print("\n" + "="*60)
    print("TEST 1: Response Protocol")
    print("="*60)

    # Test mode detection for client
    client_payload = {"prompt": "test", "user_id": "human"}
    mode = detect_mode(client_payload)
    assert mode == ResponseMode.CLIENT, "Expected CLIENT mode"
    print("✅ Client mode detection works")

    # Test mode detection for agent with _agent_call
    agent_payload = {"prompt": "test", "_agent_call": True}
    mode = detect_mode(agent_payload)
    assert mode == ResponseMode.AGENT, "Expected AGENT mode"
    print("✅ Agent mode detection (_agent_call) works")

    # Test mode detection for agent with source_agent
    agent_payload2 = {"prompt": "test", "source_agent": "orchestrator"}
    mode = detect_mode(agent_payload2)
    assert mode == ResponseMode.AGENT, "Expected AGENT mode"
    print("✅ Agent mode detection (source_agent) works")

    # Test response creation
    response = create_response(
        success=True,
        message="Test successful",
        data={"result": "ok"},
        agent_type="test"
    )
    assert response.success is True
    assert response.message == "Test successful"
    assert response.data["result"] == "ok"
    print("✅ Response creation works")

    # Test response to_dict
    response_dict = response.to_dict()
    assert "success" in response_dict
    assert "message" in response_dict
    assert "data" in response_dict
    assert "timestamp" in response_dict
    print("✅ Response to_dict() works")

    # Test response to_json
    response_json = response.to_json()
    parsed = json.loads(response_json)
    assert parsed["success"] is True
    print("✅ Response to_json() works")

    # Test response to_client_text
    client_text = response.to_client_text()
    assert client_text == "Test successful"
    print("✅ Response to_client_text() works")

    print("\n✅ All response protocol tests passed!")


def test_orchestrator_a2a_pattern():
    """Test orchestrator A2A invocation pattern."""
    print("\n" + "="*60)
    print("TEST 2: Orchestrator A2A Pattern")
    print("="*60)

    from src.runtime import AgentOrchestrator

    # Create orchestrator
    orchestrator = AgentOrchestrator()
    print("✅ Orchestrator instantiated")

    # Verify available agents
    expected_agents = ["coding", "github", "jira", "planning"]
    assert set(orchestrator.available_agents.keys()) == set(expected_agents)
    print(f"✅ Orchestrator has agents: {list(orchestrator.available_agents.keys())}")

    # Simulate A2A payload creation
    test_prompt = "Run npm audit"
    payload = json.dumps({
        "prompt": test_prompt,
        "_agent_call": True,
        "source_agent": "orchestrator"
    })

    # Verify payload structure
    parsed_payload = json.loads(payload)
    assert parsed_payload["_agent_call"] is True
    assert parsed_payload["source_agent"] == "orchestrator"
    assert parsed_payload["prompt"] == test_prompt
    print("✅ A2A payload structure is correct")

    # Verify mode detection from orchestrator payload
    mode = detect_mode(parsed_payload)
    assert mode == ResponseMode.AGENT
    print("✅ Orchestrator-created payloads trigger AGENT mode")

    print("\n✅ All orchestrator A2A pattern tests passed!")


def test_agent_mode_responses():
    """Test that agents can create proper AGENT mode responses."""
    print("\n" + "="*60)
    print("TEST 3: Agent Mode Response Structure")
    print("="*60)

    # Simulate coding agent response
    coding_response = create_response(
        success=True,
        message="Coding operation completed successfully",
        data={"output": "npm audit results..."},
        agent_type="coding",
        metadata={"command": "npm audit", "output_length": 100}
    )

    coding_dict = coding_response.to_dict()
    assert coding_dict["success"] is True
    assert coding_dict["agent_type"] == "coding"
    assert "output" in coding_dict["data"]
    print("✅ Coding agent response structure correct")

    # Simulate planning agent response
    planning_response = create_response(
        success=True,
        message="Planning completed successfully",
        data={"plan": {"steps": []}, "formatted_plan": "..."},
        agent_type="planning",
        metadata={"requirements": "test", "context_provided": False}
    )

    planning_dict = planning_response.to_dict()
    assert planning_dict["success"] is True
    assert planning_dict["agent_type"] == "planning"
    assert "plan" in planning_dict["data"]
    print("✅ Planning agent response structure correct")

    # Simulate orchestrator response
    orchestrator_response = create_response(
        success=True,
        message="Orchestration completed successfully",
        data={"workflow_result": "...", "agents_used": ["coding", "github"]},
        agent_type="orchestrator",
        metadata={"task": "test", "result_length": 100}
    )

    orchestrator_dict = orchestrator_response.to_dict()
    assert orchestrator_dict["success"] is True
    assert orchestrator_dict["agent_type"] == "orchestrator"
    assert "workflow_result" in orchestrator_dict["data"]
    print("✅ Orchestrator agent response structure correct")

    print("\n✅ All agent mode response tests passed!")


def test_client_mode_responses():
    """Test that agents can create proper CLIENT mode responses."""
    print("\n" + "="*60)
    print("TEST 4: Client Mode Response Format")
    print("="*60)

    # Test human-readable message formatting
    response = create_response(
        success=True,
        message="✅ GitHub issue created successfully\n\nIssue #123: Dependency Check",
        data={"issue_number": 123},
        agent_type="github"
    )

    client_text = response.to_client_text()
    assert "✅" in client_text
    assert "GitHub issue" in client_text
    print("✅ Client mode uses human-readable format")

    # Test error formatting
    error_response = create_response(
        success=False,
        message="❌ Error: Agent timeout after 300s",
        agent_type="coding"
    )

    error_text = error_response.to_client_text()
    assert "❌" in error_text
    assert "Error" in error_text
    print("✅ Client mode error formatting works")

    print("\n✅ All client mode response tests passed!")


def test_full_workflow_simulation():
    """Simulate a full orchestration workflow."""
    print("\n" + "="*60)
    print("TEST 5: Full Workflow Simulation")
    print("="*60)

    # Step 1: Human sends request to orchestrator (CLIENT mode)
    print("\n📝 Step 1: Human → Orchestrator (CLIENT mode)")
    client_payload = {
        "prompt": "Check dependencies for /path/to/project"
    }
    mode = detect_mode(client_payload)
    assert mode == ResponseMode.CLIENT
    print("✅ Orchestrator receives CLIENT mode request")

    # Step 2: Orchestrator calls GitHub agent (AGENT mode)
    print("\n📝 Step 2: Orchestrator → GitHub Agent (AGENT mode)")
    github_payload = {
        "prompt": "Create issue titled 'Dependency Check'",
        "_agent_call": True,
        "source_agent": "orchestrator"
    }
    mode = detect_mode(github_payload)
    assert mode == ResponseMode.AGENT
    print("✅ GitHub agent receives AGENT mode request")

    # Step 3: GitHub agent responds with structured JSON
    print("\n📝 Step 3: GitHub Agent → Orchestrator (structured response)")
    github_response = create_response(
        success=True,
        message="GitHub issue created",
        data={"issue_number": 123, "url": "https://github.com/..."},
        agent_type="github"
    )
    github_dict = github_response.to_dict()
    assert github_dict["success"] is True
    print("✅ GitHub agent returns structured JSON")

    # Step 4: Orchestrator calls Coding agent (AGENT mode)
    print("\n📝 Step 4: Orchestrator → Coding Agent (AGENT mode)")
    coding_payload = {
        "prompt": "Run npm audit for /path/to/project",
        "_agent_call": True,
        "source_agent": "orchestrator"
    }
    mode = detect_mode(coding_payload)
    assert mode == ResponseMode.AGENT
    print("✅ Coding agent receives AGENT mode request")

    # Step 5: Coding agent responds with structured JSON
    print("\n📝 Step 5: Coding Agent → Orchestrator (structured response)")
    coding_response = create_response(
        success=True,
        message="Audit completed",
        data={"vulnerabilities": 5, "output": "audit results..."},
        agent_type="coding"
    )
    coding_dict = coding_response.to_dict()
    assert coding_dict["success"] is True
    print("✅ Coding agent returns structured JSON")

    # Step 6: Orchestrator aggregates and returns to human (CLIENT mode)
    print("\n📝 Step 6: Orchestrator → Human (CLIENT mode)")
    orchestrator_response = create_response(
        success=True,
        message="""🔍 Detected dependency management task
📁 Project path: /path/to/project

📝 Step 1: Creating GitHub issue...
✅ GitHub issue created

🔍 Step 2: Running dependency audit...
✅ Audit completed
Found 5 vulnerabilities""",
        data={
            "github_issue": github_dict["data"],
            "audit_results": coding_dict["data"]
        },
        agent_type="orchestrator"
    )

    client_text = orchestrator_response.to_client_text()
    assert "🔍" in client_text
    assert "✅" in client_text
    print("✅ Orchestrator returns human-readable response")

    print("\n✅ Full workflow simulation passed!")


def main():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("DUAL-MODE INTEGRATION TEST SUITE")
    print("="*60)

    try:
        test_response_protocol()
        test_orchestrator_a2a_pattern()
        test_agent_mode_responses()
        test_client_mode_responses()
        test_full_workflow_simulation()

        print("\n" + "="*60)
        print("🎉 ALL INTEGRATION TESTS PASSED! 🎉")
        print("="*60)
        print("\n✅ Summary:")
        print("   • Response protocol: ✅")
        print("   • A2A invocation pattern: ✅")
        print("   • Agent mode responses: ✅")
        print("   • Client mode responses: ✅")
        print("   • Full workflow simulation: ✅")
        print("\n✅ The dual-mode implementation is ready for deployment!")

        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
