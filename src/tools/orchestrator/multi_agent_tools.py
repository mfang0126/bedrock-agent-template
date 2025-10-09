"""
Enhanced coordinator with actual agent invocation using boto3.

Based on AWS AgentCore multi-agent samples.
"""

import os
import json
from typing import Dict, Optional
from strands.tools import tool
import boto3
from botocore.exceptions import ClientError


# Initialize AgentCore client on-demand (lazy loading)
def get_agentcore_client():
    """Get or create the AgentCore boto3 client"""
    return boto3.client(
        'bedrock-agentcore',
        region_name=os.getenv("AWS_REGION", "ap-southeast-2")
    )


@tool
async def invoke_github_agent(prompt: str, user_id: str = "orchestrator") -> str:
    """
    Invoke the GitHub agent to perform repository operations.

    Args:
        prompt: The task for the GitHub agent
        user_id: User ID for the operation

    Returns:
        Response from the GitHub agent
    """
    agent_arn = os.getenv("GITHUB_AGENT_ARN", "")

    if not agent_arn:
        return "❌ GitHub Agent ARN not configured. Deploy the GitHub agent first and set GITHUB_AGENT_ARN environment variable."

    try:
        # Get AgentCore client
        client = get_agentcore_client()

        # Use full ARN with invoke_agent_runtime (AgentCore API)
        boto3_response = client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            qualifier="DEFAULT",
            payload=json.dumps({"prompt": prompt})
        )

        # Parse event-stream response
        result = ""
        if "text/event-stream" in boto3_response.get("contentType", ""):
            for line in boto3_response["response"].iter_lines(chunk_size=1):
                if line:
                    line = line.decode("utf-8")
                    # Skip "data: " prefix
                    line = line[6:]
                    # Remove surrounding quotes if present
                    if line.startswith('"') and line.endswith('"'):
                        line = line[1:-1]
                    # Unescape newlines
                    line = line.replace('\\n', '\n')
                    result += line
        else:
            # Handle non-streaming response
            response_body = boto3_response['response'].read()
            response_data = json.loads(response_body)
            result = response_data

        return f"✅ GitHub Agent Response:\n{result}"

    except ClientError as e:
        return f"❌ Error invoking GitHub agent: {e.response['Error']['Message']}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"


@tool
async def invoke_planning_agent(prompt: str, context: Optional[str] = None) -> str:
    """
    Invoke the Planning agent to generate implementation plans.

    Args:
        prompt: The planning request
        context: Optional context from previous agents

    Returns:
        Response from the Planning agent
    """
    agent_arn = os.getenv("PLANNING_AGENT_ARN", "")

    if not agent_arn:
        return "❌ Planning Agent ARN not configured. Deploy the Planning agent first and set PLANNING_AGENT_ARN environment variable."

    try:
        # Get AgentCore client
        client = get_agentcore_client()

        # Include context if provided
        full_prompt = prompt
        if context:
            full_prompt = f"Context from previous agent:\n{context}\n\nRequest:\n{prompt}"

        # Use full ARN with invoke_agent_runtime (AgentCore API)
        boto3_response = client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            qualifier="DEFAULT",
            payload=json.dumps({"prompt": full_prompt})
        )

        # Parse event-stream response
        result = ""
        if "text/event-stream" in boto3_response.get("contentType", ""):
            for line in boto3_response["response"].iter_lines(chunk_size=1):
                if line:
                    line = line.decode("utf-8")
                    # Skip "data: " prefix
                    line = line[6:]
                    # Remove surrounding quotes if present
                    if line.startswith('"') and line.endswith('"'):
                        line = line[1:-1]
                    # Unescape newlines
                    line = line.replace('\\n', '\n')
                    result += line
        else:
            # Handle non-streaming response
            response_body = boto3_response['response'].read()
            response_data = json.loads(response_body)
            result = response_data

        return f"✅ Planning Agent Response:\n{result}"

    except ClientError as e:
        return f"❌ Error invoking Planning agent: {e.response['Error']['Message']}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"


@tool
async def execute_multi_agent_workflow(
    agents: list,
    initial_prompt: str,
    pass_context: bool = True
) -> str:
    """
    Execute a sequence of agent calls, optionally passing context between them.
    
    Args:
        agents: List of agent names to invoke in sequence
        initial_prompt: The initial prompt to start the workflow
        pass_context: Whether to pass previous agent outputs as context
        
    Returns:
        Combined results from all agents
    """
    results = []
    context = ""
    current_prompt = initial_prompt
    
    agent_functions = {
        "github": invoke_github_agent,
        "planning": invoke_planning_agent,
        # Add more agents here as they're implemented
    }
    
    for agent_name in agents:
        if agent_name not in agent_functions:
            results.append(f"⚠️ Unknown agent: {agent_name}")
            continue
        
        agent_func = agent_functions[agent_name]
        
        # Prepare prompt with context if enabled
        if pass_context and context:
            agent_prompt = f"{current_prompt}\n\nPrevious context:\n{context}"
        else:
            agent_prompt = current_prompt
        
        # Invoke the agent
        result = await agent_func(agent_prompt)
        results.append(f"\n{'='*50}\n{agent_name.upper()} AGENT\n{'='*50}\n{result}")
        
        # Update context for next agent
        if pass_context:
            context = result
    
    return "\n".join(results)


@tool
async def check_agent_status() -> str:
    """
    Check which agents are configured and available.
    
    Returns:
        Status of all agent configurations
    """
    agents = {
        "GitHub": os.getenv("GITHUB_AGENT_ARN", "Not configured"),
        "Planning": os.getenv("PLANNING_AGENT_ARN", "Not configured"),
        "JIRA": os.getenv("JIRA_AGENT_ARN", "Not configured"),
        "Coding": os.getenv("CODING_AGENT_ARN", "Not configured"),
    }
    
    status = ["📊 Agent Configuration Status:\n"]
    for name, arn in agents.items():
        if arn and arn != "Not configured":
            status.append(f"✅ {name}: {arn}")
        else:
            status.append(f"❌ {name}: Not configured")
    
    status.append("\n💡 To configure agents:")
    status.append("1. Deploy each agent: poe deploy-github, poe deploy-planning, etc.")
    status.append("2. Get ARNs: agentcore status --agent <agent_name>")
    status.append("3. Set environment variables: export GITHUB_AGENT_ARN='arn:...'")
    
    return "\n".join(status)
