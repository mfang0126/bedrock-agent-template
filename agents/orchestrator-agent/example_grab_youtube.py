#!/usr/bin/env python
"""
Example: Using the Orchestrator for grab-youtube dependency management.

This example shows how the orchestrator coordinates agents to check and fix
dependencies for your grab-youtube project.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from runtime import orchestrator


def check_grab_youtube_dependencies():
    """
    Check and fix dependencies for the grab-youtube project.
    
    This demonstrates the full workflow:
    1. Create GitHub issue for tracking
    2. Run dependency audit
    3. Attempt fixes (up to 3 times)
    4. Create blocker issue if fixes fail
    5. Update Jira status
    """
    
    print("🎬 Grab-YouTube Dependency Check Workflow")
    print("=" * 60)
    
    # Project details
    project_path = "/Users/mingfang/Code/grab-youtube"
    feature_name = "video-download-optimization"
    
    print(f"📁 Project: {project_path}")
    print(f"✨ Feature: {feature_name}")
    print("\n" + "-" * 60)
    
    print("\n📋 Workflow Steps:")
    print("   1. Create GitHub issue to track the work")
    print("   2. Run npm/yarn audit to check for vulnerabilities")
    print("   3. Try to fix vulnerabilities (up to 3 attempts)")
    print("   4. If fixes succeed, commit the changes")
    print("   5. If fixes fail, create detailed GitHub issue")
    print("   6. Update Jira with final status")
    
    print("\n" + "-" * 60)
    print("🚀 Executing workflow...")
    print("-" * 60 + "\n")
    
    # Build the request for the orchestrator
    request = f"""Check dependencies for {project_path} and fix any vulnerabilities found.
    This is for the feature: {feature_name}.
    Create GitHub issues to track the work and update Jira when done."""
    
    # Execute the request
    result = orchestrator.orchestrate_task(request)
    
    print("\n" + "=" * 60)
    print("📊 Workflow Execution Results:")
    print("=" * 60)
    print(result)
    
    # Expected outcomes
    print("\n" + "-" * 60)
    print("📌 Expected Outcomes:")
    print("-" * 60)
    print("✅ If all vulnerabilities were fixed:")
    print("   - package.json and lock files updated")
    print("   - Changes committed with descriptive message")
    print("   - GitHub issue closed")
    print("   - Jira status: In Progress")
    print("\n❌ If some vulnerabilities couldn't be fixed:")
    print("   - Detailed GitHub issue created with:")
    print("     • List of remaining vulnerabilities")
    print("     • Failed fix attempts documentation")
    print("     • Recommended manual interventions")
    print("   - Jira status: Blocked")
    print("   - Team notified of blockers")
    
    return result


def test_individual_agents():
    """Test calling individual agents."""
    print("\n" + "=" * 60)
    print("Testing Individual Agent Calls")
    print("=" * 60)
    
    tests = [
        ("planning", "Break down the task of adding user authentication"),
        ("coding", "Show me the package.json file for /Users/mingfang/Code/grab-youtube"),
        ("github", "List my recent GitHub issues"),
        ("jira", "Show current sprint status")
    ]
    
    for agent_name, prompt in tests:
        print(f"\n📍 Testing {agent_name} agent:")
        print(f"   Prompt: {prompt}")
        result = orchestrator.call_agent(agent_name, prompt)
        if result["success"]:
            print(f"   ✅ Success")
            response_preview = result["response"][:200] + "..." if len(result["response"]) > 200 else result["response"]
            print(f"   Response: {response_preview}")
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")


def main():
    """Main execution."""
    try:
        print("\n" + "=" * 60)
        print("🎯 Master Orchestrator - Grab-YouTube Dependency Management")
        print("Coordinating Multiple Specialized Agents")
        print("=" * 60 + "\n")
        
        # Test individual agents first
        print("First, let's test individual agent connections...")
        test_individual_agents()
        
        # Then run the full workflow
        print("\n" + "=" * 60)
        print("Now running the full dependency check workflow...")
        print("=" * 60)
        
        result = check_grab_youtube_dependencies()
        
        print("\n" + "=" * 60)
        print("✨ Workflow Completed!")
        print("\nThe orchestrator successfully coordinated:")
        print("• Task analysis and routing")
        print("• Agent selection based on task type")
        print("• Sequential execution of workflow steps")
        print("• Error handling and fallback strategies")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Ensure all agents are properly installed")
        print("2. Check that agent directories exist")
        print("3. Verify project path exists")
        print("4. Make sure Python environment is set up correctly")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Custom prompt mode
        custom_prompt = " ".join(sys.argv[1:])
        print(f"\n🔧 Running with custom prompt: {custom_prompt}")
        print("-" * 60)
        result = orchestrator.orchestrate_task(custom_prompt)
        print(result)
    else:
        # Run full example
        main()
