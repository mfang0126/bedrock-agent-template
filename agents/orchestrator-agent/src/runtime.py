"""
Master Orchestrator Agent Runtime - Simplified implementation without Strands workflow

Coordinates multiple specialized agents through direct subprocess calls.
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Create the AgentCore app
app = BedrockAgentCoreApp()


class AgentOrchestrator:
    """Orchestrates calls to specialized agents."""
    
    def __init__(self):
        self.agents_base_path = Path(__file__).parent.parent.parent
        self.available_agents = {
            "coding": "coding-agent",
            "github": "github-agent", 
            "jira": "jira-agent",
            "planning": "planning-agent"
        }
        logger.info(f"Orchestrator initialized with agents: {list(self.available_agents.keys())}")
    
    def call_agent(self, agent_name: str, prompt: str, timeout: int = 300) -> Dict[str, Any]:
        """Call a specialized agent with a prompt."""
        if agent_name not in self.available_agents:
            return {
                "success": False,
                "error": f"Unknown agent: {agent_name}. Available: {list(self.available_agents.keys())}",
                "response": ""
            }
        
        agent_dir = self.agents_base_path / self.available_agents[agent_name]
        
        if not agent_dir.exists():
            return {
                "success": False,
                "error": f"Agent directory not found: {agent_dir}",
                "response": ""
            }
        
        payload = json.dumps({"prompt": prompt})
        
        # Try different command patterns based on what's available
        commands_to_try = [
            ["python", "-m", "bedrock_agentcore.cli", "invoke", payload, "--user-id", "orchestrator"],
            ["python", "src/runtime.py"],  # Direct runtime invocation
            ["agentcore", "invoke", payload, "--user-id", "orchestrator"],
        ]
        
        for cmd in commands_to_try:
            try:
                logger.info(f"Calling {agent_name} agent with command: {' '.join(cmd[:2])}...")
                
                # For direct runtime invocation, pass payload via stdin
                if "runtime.py" in str(cmd):
                    result = subprocess.run(
                        cmd,
                        input=payload,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        cwd=str(agent_dir)
                    )
                else:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        cwd=str(agent_dir)
                    )
                
                if result.returncode == 0:
                    return {
                        "success": True,
                        "agent": agent_name,
                        "response": result.stdout.strip()
                    }
                
                logger.debug(f"Command failed with return code {result.returncode}")
                
            except subprocess.TimeoutExpired:
                logger.error(f"{agent_name} agent timed out after {timeout}s")
                return {
                    "success": False,
                    "error": f"Timeout after {timeout}s",
                    "response": ""
                }
            except Exception as e:
                logger.debug(f"Command failed: {e}")
                continue
        
        # If all commands failed
        return {
            "success": False,
            "error": f"Failed to invoke {agent_name} agent",
            "response": ""
        }
    
    def create_dependency_workflow(self, project_path: str, feature_name: str) -> str:
        """Create a dependency check workflow plan."""
        workflow = f"""
📋 Dependency Check Workflow for: {feature_name}
📁 Project: {project_path}

Workflow Steps:
1. Create GitHub Issue - Track the feature work
2. Dependency Audit - Check for vulnerabilities
3. Fix Attempts - Try to fix vulnerabilities (max 3 attempts)
4. Commit or Create Issue - Based on fix results
5. Update Jira - Report final status

This workflow will coordinate between:
- Coding Agent: Run audits and fixes
- GitHub Agent: Create issues and commits
- Jira Agent: Update project tracking
"""
        return workflow
    
    def orchestrate_task(self, task: str) -> str:
        """Orchestrate a task by analyzing it and delegating to appropriate agents."""
        response = []
        
        # Analyze the task to determine which agents to use
        task_lower = task.lower()
        
        # Determine workflow based on keywords
        if any(word in task_lower for word in ["dependency", "dependencies", "audit", "vulnerability"]):
            response.append("🔍 Detected dependency management task")
            
            # Extract project path if mentioned
            project_path = "/Users/mingfang/Code/grab-youtube"  # Default
            if "/users/" in task_lower or "/home/" in task_lower:
                # Try to extract path from task
                import re
                path_match = re.search(r'(/[^\s]+)', task)
                if path_match:
                    project_path = path_match.group(1)
            
            response.append(f"📁 Project path: {project_path}")
            
            # Step 1: Create GitHub issue
            response.append("\n📝 Step 1: Creating GitHub issue...")
            github_result = self.call_agent(
                "github",
                f"Create an issue titled 'Dependency Check' with labels 'dependencies', 'audit'"
            )
            if github_result["success"]:
                response.append(f"✅ GitHub issue created")
            else:
                response.append(f"⚠️ GitHub issue creation failed: {github_result.get('error', 'Unknown error')}")
            
            # Step 2: Run dependency audit
            response.append("\n🔍 Step 2: Running dependency audit...")
            audit_result = self.call_agent(
                "coding",
                f"Run dependency audit for the Node.js project at {project_path}. Check if it uses npm or yarn and run the appropriate audit command."
            )
            if audit_result["success"]:
                response.append(f"✅ Audit completed")
                response.append(audit_result["response"][:500] + "..." if len(audit_result["response"]) > 500 else audit_result["response"])
            else:
                response.append(f"⚠️ Audit failed: {audit_result.get('error', 'Unknown error')}")
            
            # Step 3: Attempt fixes
            response.append("\n🔧 Step 3: Attempting to fix vulnerabilities...")
            fix_result = self.call_agent(
                "coding",
                f"Try to fix dependency vulnerabilities in {project_path}. Use npm audit fix or yarn audit fix."
            )
            if fix_result["success"]:
                response.append(f"✅ Fix attempt completed")
            else:
                response.append(f"⚠️ Fix attempt failed: {fix_result.get('error', 'Unknown error')}")
            
            # Step 4: Update Jira
            response.append("\n📋 Step 4: Updating Jira...")
            jira_result = self.call_agent(
                "jira",
                "Update the current sprint with dependency audit results"
            )
            if jira_result["success"]:
                response.append(f"✅ Jira updated")
            else:
                response.append(f"⚠️ Jira update failed: {jira_result.get('error', 'Unknown error')}")
                
        elif any(word in task_lower for word in ["plan", "breakdown", "design", "architect"]):
            response.append("📋 Detected planning task")
            planning_result = self.call_agent("planning", task)
            if planning_result["success"]:
                response.append(planning_result["response"])
            else:
                response.append(f"⚠️ Planning failed: {planning_result.get('error', 'Unknown error')}")
                
        elif any(word in task_lower for word in ["github", "issue", "pull request", "pr", "commit"]):
            response.append("🐙 Detected GitHub task")
            github_result = self.call_agent("github", task)
            if github_result["success"]:
                response.append(github_result["response"])
            else:
                response.append(f"⚠️ GitHub operation failed: {github_result.get('error', 'Unknown error')}")
                
        elif any(word in task_lower for word in ["jira", "ticket", "sprint", "story"]):
            response.append("📋 Detected Jira task")
            jira_result = self.call_agent("jira", task)
            if jira_result["success"]:
                response.append(jira_result["response"])
            else:
                response.append(f"⚠️ Jira operation failed: {jira_result.get('error', 'Unknown error')}")
                
        elif any(word in task_lower for word in ["code", "run", "execute", "test", "debug"]):
            response.append("💻 Detected coding task")
            coding_result = self.call_agent("coding", task)
            if coding_result["success"]:
                response.append(coding_result["response"])
            else:
                response.append(f"⚠️ Coding operation failed: {coding_result.get('error', 'Unknown error')}")
        else:
            # Default: try planning agent first to break down the task
            response.append("🤔 Analyzing task with planning agent...")
            planning_result = self.call_agent("planning", f"Break down this task: {task}")
            if planning_result["success"]:
                response.append(planning_result["response"])
            else:
                response.append("I'll help you with that task. Let me coordinate the appropriate agents.")
        
        return "\n".join(response)


# Create orchestrator instance
orchestrator = AgentOrchestrator()


def _extract_user_input(payload):
    """Extract user input from various possible payload formats."""
    if not isinstance(payload, dict):
        logger.warning(f"Invalid payload type: {type(payload)}")
        return ""
    
    # Try common payload keys in order of preference
    for key in ["prompt", "input", "message", "text", "query"]:
        value = payload.get(key, "")
        if value and isinstance(value, str) and value.strip():
            return value.strip()
    
    logger.warning(f"No valid input found in payload keys: {list(payload.keys())}")
    return ""


@app.entrypoint
async def strands_agent_orchestrator(payload: Dict[str, Any]):
    """
    Master Orchestrator Agent entrypoint.
    
    Coordinates complex workflows between specialized agents.
    """
    try:
        # Extract user input from payload
        user_input = _extract_user_input(payload)
        
        # Validate input
        if not user_input:
            logger.info("Empty input received, returning greeting message")
            yield """Hello! I'm the Master Orchestrator Agent.

I coordinate between specialized agents to accomplish complex tasks:
• **Coding Agent**: Code execution, dependency management, testing
• **GitHub Agent**: Issues, PRs, commits, repository management
• **Jira Agent**: Project tracking and team communication
• **Planning Agent**: Task breakdown and implementation planning

Available commands:
- "Check dependencies for /path/to/project" - Run dependency audit and fixes
- "Plan a new feature: [description]" - Break down feature into tasks
- "Create GitHub issue for [topic]" - Create and track GitHub issues
- "Update Jira sprint" - Update project tracking

What would you like me to orchestrate?"""
            return
        
        logger.info(f"📥 Processing orchestrator request: {user_input}")
        
        # Process the request
        result = orchestrator.orchestrate_task(user_input)
        
        # Yield the result
        yield result
    
    except Exception as e:
        logger.error(f"Orchestrator Agent error: {str(e)}", exc_info=True)
        yield f"❌ Error in orchestrator: {str(e)}"


if __name__ == "__main__":
    # Test mode
    if len(sys.argv) > 1:
        test_prompt = " ".join(sys.argv[1:])
        print(f"Testing with prompt: {test_prompt}")
        result = orchestrator.orchestrate_task(test_prompt)
        print(result)
    else:
        app.run()
