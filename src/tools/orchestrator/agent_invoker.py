"""
Agent invocation utilities for calling other AgentCore agents via boto3.

Based on AWS AgentCore multi-agent samples.
"""

import os
import json
import boto3
from typing import Dict, Optional, Any
from botocore.exceptions import ClientError


class AgentInvoker:
    """Handles invocation of other AgentCore agents using boto3."""
    
    def __init__(self, region: str = "ap-southeast-2"):
        """Initialize the agent invoker with boto3 client."""
        self.client = boto3.client(
            'bedrock-agent-runtime',
            region_name=region
        )
        
        # Agent ARNs from environment or hardcoded after deployment
        self.agent_arns = {
            "github": os.getenv("GITHUB_AGENT_ARN", ""),
            "planning": os.getenv("PLANNING_AGENT_ARN", ""),
            "jira": os.getenv("JIRA_AGENT_ARN", ""),
            "coding": os.getenv("CODING_AGENT_ARN", ""),
        }
    
    def invoke_agent(
        self,
        agent_name: str,
        prompt: str,
        user_id: str = "orchestrator",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Invoke an AgentCore agent and return its response.
        
        Args:
            agent_name: Name of the agent to invoke (github, planning, jira, coding)
            prompt: The prompt to send to the agent
            user_id: User ID for the agent invocation
            session_id: Optional session ID for conversation continuity
            
        Returns:
            Dict containing the agent's response
        """
        agent_arn = self.agent_arns.get(agent_name)
        if not agent_arn:
            return {
                "error": f"Agent ARN not configured for: {agent_name}",
                "available_agents": list(self.agent_arns.keys())
            }
        
        try:
            # Prepare the request
            request_params = {
                "agentId": agent_arn.split("/")[-1],  # Extract agent ID from ARN
                "agentAliasId": "TSTALIASID",  # Default test alias
                "inputText": prompt,
                "enableTrace": True
            }
            
            if session_id:
                request_params["sessionId"] = session_id
            
            # Invoke the agent
            response = self.client.invoke_agent(**request_params)
            
            # Parse the streaming response
            result_text = ""
            for event in response.get("completion", []):
                if "chunk" in event:
                    chunk = event["chunk"]
                    if "bytes" in chunk:
                        result_text += chunk["bytes"].decode("utf-8")
            
            return {
                "success": True,
                "agent": agent_name,
                "response": result_text,
                "session_id": response.get("sessionId")
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            return {
                "success": False,
                "agent": agent_name,
                "error": f"{error_code}: {error_message}",
                "hint": "Make sure the agent is deployed and the ARN is correct"
            }
        except Exception as e:
            return {
                "success": False,
                "agent": agent_name,
                "error": str(e)
            }
    
    def invoke_github_agent(self, prompt: str, user_id: str = "orchestrator") -> Dict:
        """Convenience method to invoke GitHub agent."""
        return self.invoke_agent("github", prompt, user_id)
    
    def invoke_planning_agent(self, prompt: str, user_id: str = "orchestrator") -> Dict:
        """Convenience method to invoke Planning agent."""
        return self.invoke_agent("planning", prompt, user_id)
    
    def invoke_jira_agent(self, prompt: str, user_id: str = "orchestrator") -> Dict:
        """Convenience method to invoke JIRA agent."""
        return self.invoke_agent("jira", prompt, user_id)
    
    def invoke_coding_agent(self, prompt: str, user_id: str = "orchestrator") -> Dict:
        """Convenience method to invoke Coding agent."""
        return self.invoke_agent("coding", prompt, user_id)


# Global invoker instance
agent_invoker = AgentInvoker()
