"""
Coding Agent - Main Entry Point

Entry point for running the coding agent with AgentCore.
"""

import os
import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from coding_agent import create_coding_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the coding agent"""
    try:
        # Create and initialize the agent
        agent = create_coding_agent()
        
        logger.info(f"Coding Agent initialized successfully")
        logger.info(f"Agent tools: {[tool.__name__ for tool in agent.tools]}")
        
        # The agent will be managed by AgentCore runtime
        return agent
        
    except Exception as e:
        logger.error(f"Failed to initialize coding agent: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
