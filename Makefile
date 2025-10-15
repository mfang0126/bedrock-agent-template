.PHONY: help test test-all test-coding test-github test-jira deploy invoke clean

# Default target
help:
	@echo "Agent Testing & Deployment Commands"
	@echo ""
	@echo "Local Testing (no AWS):"
	@echo "  make test-coding     - Test Coding agent locally"
	@echo "  make test-github     - Test GitHub agent locally (mock auth)"
	@echo "  make test-jira       - Test JIRA agent locally (mock auth)"
	@echo "  make test-all        - Test all agents locally"
	@echo ""
	@echo "AWS Testing (deployed):"
	@echo "  make invoke-coding   - Invoke deployed Coding agent"
	@echo "  make invoke-github   - Invoke deployed GitHub agent"
	@echo "  make invoke-jira     - Invoke deployed JIRA agent"
	@echo ""
	@echo "Deployment:"
	@echo "  make setup           - Setup shared AWS resources"
	@echo "  make deploy          - Deploy all agents to AWS"
	@echo "  make deploy-agent A=<name> - Deploy specific agent"
	@echo ""
	@echo "Utility:"
	@echo "  make clean           - Clean up temporary files"
	@echo "  make status          - Show agent status"

# Local Testing (no AWS required)
test-coding:
	@uv run scripts/test_coding_local.py 'what can you do'

test-github:
	@uv run scripts/test_github_local.py 'what can you do'

test-jira:
	@uv run scripts/test_jira_local.py 'what can you do'

test-all: test-coding test-github test-jira
	@echo "✅ All local tests complete"

# AWS Invocation (requires deployment)
invoke-coding:
	@cd scripts && ./invoke_coding.sh 'what can you do'

invoke-github:
	@cd scripts && ./invoke_github.sh 'what can you do'

invoke-jira:
	@cd scripts && ./invoke_jira.sh 'what can you do'

# Deployment
setup:
	@cd scripts && ./setup_shared_resources.sh && ./configure_agents.sh
	@echo "✅ Setup complete. Run 'make deploy' to deploy agents."

deploy:
	@cd scripts && ./deploy_all.sh

deploy-agent:
	@if [ -z "$(A)" ]; then \
		echo "Error: Specify agent with A=<name>"; \
		echo "Example: make deploy-agent A=coding"; \
		exit 1; \
	fi
	@uv run agentcore launch --agent $(A)

# Utility
clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleaned up temporary files"

status:
	@echo "Checking agent status..."
	@uv run agentcore status --agent coding || true
	@uv run agentcore status --agent github || true
	@uv run agentcore status --agent jira || true
	@uv run agentcore status --agent orchestrator || true
	@uv run agentcore status --agent planning || true

# Interactive testing (prompts for input)
test-coding-interactive:
	@read -p "Enter prompt: " prompt; \
	uv run scripts/test_coding_local.py "$$prompt"

test-github-interactive:
	@read -p "Enter prompt: " prompt; \
	uv run scripts/test_github_local.py "$$prompt"

test-jira-interactive:
	@read -p "Enter prompt: " prompt; \
	uv run scripts/test_jira_local.py "$$prompt"
