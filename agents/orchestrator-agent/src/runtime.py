"""
Master Orchestrator Agent Runtime - Dual-mode client/agent communication

Coordinates multiple specialized agents through AWS Lambda invocations.
Supports both human client streaming and agent-to-agent structured responses.
"""

import os
import sys
import json
import logging
import boto3
import uuid
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
from src.response_protocol import (
    ResponseMode,
    create_response,
    detect_mode,
)

# AWS Configuration
AWS_REGION = 'ap-southeast-2'
# ✅ CORRECT CLIENT: Use 'bedrock-agentcore' (not 'bedrock-agent-runtime')
BEDROCK_AGENTCORE_CLIENT = boto3.client('bedrock-agentcore', region_name=AWS_REGION)

# Create the AgentCore app
app = BedrockAgentCoreApp()


class AgentOrchestrator:
    """
    Orchestrates calls to specialized agents via AWS Lambda invocation.

    Uses boto3 AWS SDK for Lambda-to-Lambda communication instead of
    subprocess calls, enabling proper agent coordination in AWS environment.
    """

    def __init__(self):
        # Map agent names to their FULL ARNs (from .bedrock_agentcore.yaml files)
        # Only include agents that are currently deployed
        self.agent_arns = {
            "coding": "arn:aws:bedrock-agentcore:ap-southeast-2:670326884047:runtime/codingagent-lE7IQU3dK8",
            "planning": "arn:aws:bedrock-agentcore:ap-southeast-2:670326884047:runtime/planning-jDw1hm2ip6",
            "github": "arn:aws:bedrock-agentcore:ap-southeast-2:670326884047:runtime/github-Hn7UKwBMRj",
            "jira": "arn:aws:bedrock-agentcore:ap-southeast-2:670326884047:runtime/jira_agent-WboCCb8qfb",
        }

        logger.info(f"Orchestrator initialized with agents: {list(self.agent_arns.keys())}")
    
    def call_agent(
        self,
        agent_name: str,
        prompt: str,
        session_id: Optional[str] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Call a specialized agent via AWS Lambda invocation.

        Adds A2A markers to trigger AGENT mode in called agents:
        - _agent_call: true
        - source_agent: "orchestrator"

        Args:
            agent_name: Name of agent to call (coding, planning, github, jira)
            prompt: User prompt to forward to agent
            session_id: Optional session ID for continuity
            timeout: Timeout in seconds (note: Lambda has max 15min timeout)

        Returns:
            Dict with success, response, and optional error fields
        """

        # Validate agent exists
        if agent_name not in self.agent_arns:
            return {
                "success": False,
                "error": f"Unknown agent: {agent_name}. Available: {list(self.agent_arns.keys())}",
                "response": ""
            }

        agent_runtime_arn = self.agent_arns[agent_name]

        # Build payload with A2A markers to trigger AGENT mode
        payload = {
            "prompt": prompt,
            "_agent_call": True,          # Triggers AGENT mode
            "source_agent": "orchestrator" # Identifies caller
        }

        try:
            logger.info(f"🔗 Invoking {agent_name} agent via AgentCore...")
            logger.info(f"   ARN: {agent_runtime_arn}")
            logger.info(f"   Payload: {json.dumps(payload, indent=2)}")

            # ✅ CORRECT METHOD: Use invoke_agent_runtime with bedrock-agentcore client
            # Generate session ID (must be >= 33 chars)
            runtime_session_id = session_id or f"orchestrator-{agent_name}-{uuid.uuid4().hex[:16]}"

            response = BEDROCK_AGENTCORE_CLIENT.invoke_agent_runtime(
                agentRuntimeArn=agent_runtime_arn,
                payload=json.dumps(payload).encode('utf-8'),  # Must be bytes, not string
                contentType='application/json',
                accept='application/json',
                runtimeSessionId=runtime_session_id,
                runtimeUserId='orchestrator-agent'
            )

            # ✅ CORRECT RESPONSE HANDLING: Stream the response
            # The response is a streaming body (EventStream) of raw bytes
            result_bytes = b''
            if 'response' in response:
                # response['response'] is an EventStream, iterate to get raw bytes
                event_stream = response['response']
                for chunk in event_stream:
                    # Each chunk is raw bytes, not a dict
                    if isinstance(chunk, bytes):
                        result_bytes += chunk
                    elif isinstance(chunk, dict) and 'chunk' in chunk:
                        result_bytes += chunk['chunk']['bytes']

            result_text = result_bytes.decode('utf-8')
            logger.info(f"✅ Agent {agent_name} responded ({len(result_text)} bytes)")

            # Parse JSON response (AGENT mode should return structured JSON)
            try:
                result_json = json.loads(result_text)
                return {
                    "success": True,
                    "response": result_json,
                    "agent": agent_name
                }
            except json.JSONDecodeError:
                # Fallback if response isn't JSON
                logger.warning(f"Response from {agent_name} was not JSON, returning raw text")
                return {
                    "success": True,
                    "response": {"raw_text": result_text},
                    "agent": agent_name,
                    "warning": "Response was not structured JSON"
                }

        except Exception as e:
            logger.error(f"❌ Error invoking {agent_name}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Failed to invoke {agent_name}: {str(e)}",
                "response": "",
                "agent": agent_name
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
                result_text = str(audit_result["response"])
                response.append(result_text[:500] + "..." if len(result_text) > 500 else result_text)
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
                # Extract text from response (could be dict with raw_text or direct string)
                result_data = planning_result["response"]
                if isinstance(result_data, dict):
                    response.append(result_data.get("raw_text", str(result_data)))
                else:
                    response.append(str(result_data))
            else:
                response.append(f"⚠️ Planning failed: {planning_result.get('error', 'Unknown error')}")
                
        elif any(word in task_lower for word in ["github", "issue", "pull request", "pr", "commit"]):
            response.append("🐙 Detected GitHub task")
            github_result = self.call_agent("github", task)
            if github_result["success"]:
                response.append(str(github_result["response"]))
            else:
                response.append(f"⚠️ GitHub operation failed: {github_result.get('error', 'Unknown error')}")
                
        elif any(word in task_lower for word in ["jira", "ticket", "sprint", "story"]):
            response.append("📋 Detected Jira task")
            jira_result = self.call_agent("jira", task)
            if jira_result["success"]:
                response.append(str(jira_result["response"]))
            else:
                response.append(f"⚠️ Jira operation failed: {jira_result.get('error', 'Unknown error')}")
                
        elif any(word in task_lower for word in ["code", "run", "execute", "test", "debug"]):
            response.append("💻 Detected coding task")
            coding_result = self.call_agent("coding", task)
            if coding_result["success"]:
                response.append(str(coding_result["response"]))
            else:
                response.append(f"⚠️ Coding operation failed: {coding_result.get('error', 'Unknown error')}")
        else:
            # Default: try planning agent first to break down the task
            response.append("🤔 Analyzing task with planning agent...")
            planning_result = self.call_agent("planning", f"Break down this task: {task}")
            if planning_result["success"]:
                response.append(str(planning_result["response"]))
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


async def handle_client_mode(user_input: str) -> str:
    """Stream response for human clients with progress updates.

    Args:
        user_input: User's orchestration request

    Returns:
        Human-readable orchestration result with emoji progress markers
    """
    try:
        logger.info("🚀 Processing in CLIENT mode (streaming)...")

        # Execute orchestration workflow
        result = orchestrator.orchestrate_task(user_input)

        return result

    except Exception as e:
        error_response = create_response(
            success=False,
            message=f"❌ Error: {str(e)}",
            agent_type="orchestrator"
        )
        return error_response.to_client_text()


async def handle_agent_mode(user_input: str) -> Dict[str, Any]:
    """Execute orchestration for agent-to-agent communication.

    Args:
        user_input: Agent's orchestration command

    Returns:
        Structured JSON response with workflow results
    """
    try:
        logger.info("🤖 Processing in AGENT mode (structured)...")

        # Execute orchestration workflow
        result = orchestrator.orchestrate_task(user_input)

        # Return structured response with orchestration results
        return create_response(
            success=True,
            message="Orchestration completed successfully",
            data={
                "workflow_result": result,
                "agents_used": list(orchestrator.agent_arns.keys())
            },
            agent_type="orchestrator",
            metadata={
                "task": user_input,
                "result_length": len(result)
            }
        ).to_dict()

    except Exception as e:
        error_response = create_response(
            success=False,
            message=f"Orchestration operation failed: {str(e)}",
            agent_type="orchestrator"
        )
        return error_response.to_dict()


@app.entrypoint
async def strands_agent_orchestrator(payload: Dict[str, Any]):
    """Master Orchestrator Agent entrypoint with dual-mode support.

    Automatically detects if caller is:
    - Human client: Returns streaming text with progress markers
    - Another agent: Returns structured JSON

    Coordinates workflows between specialized agents (coding, planning, github, jira).

    Args:
        payload: Request payload with 'prompt' and optional mode indicators

    Yields:
        Streaming responses (client mode) or structured dict (agent mode)
    """
    # Detect communication mode
    mode = detect_mode(payload)
    user_input = _extract_user_input(payload)

    logger.info("\n" + "="*60)
    logger.info("📥 Orchestrator Agent Request")
    logger.info(f"   Mode: {mode.value.upper()}")
    logger.info(f"   Input: {user_input[:100]}{'...' if len(user_input) > 100 else ''}")
    logger.info("="*60 + "\n")

    # Validate input
    if not user_input:
        greeting = """Hello! I'm the Master Orchestrator Agent.

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

        if mode == ResponseMode.AGENT:
            yield create_response(
                success=True,
                message="Orchestrator ready",
                data={"greeting": greeting},
                agent_type="orchestrator"
            ).to_dict()
        else:
            yield greeting
        return

    # Execute based on mode
    if mode == ResponseMode.AGENT:
        # Agent-to-agent: Return structured response
        result = await handle_agent_mode(user_input)
        yield result
    else:
        # Client: Stream human-readable response
        result = await handle_client_mode(user_input)
        yield result


if __name__ == "__main__":
    # Test mode
    if len(sys.argv) > 1:
        test_prompt = " ".join(sys.argv[1:])
        print(f"Testing with prompt: {test_prompt}")
        result = orchestrator.orchestrate_task(test_prompt)
        print(result)
    else:
        app.run()
