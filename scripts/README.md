# Setup Scripts

Automation scripts for AWS Bedrock AgentCore deployment.

## First-Time AWS Account Setup

### `setup-new-aws-account.sh`

Complete automation for new AWS accounts. Runs all setup steps from initial configuration through deployment.

**Prerequisites:**
- AWS SSO login completed
- Python 3.10+ installed
- `uv` package manager installed

**Usage:**
```bash
# Authenticate first
authenticate --to=wealth-dev-au
# or
aws_use mingfang

# Run complete setup
./scripts/setup-new-aws-account.sh
```

**What it does:**
1. ✅ Verifies AWS credentials and prerequisites
2. 📦 Installs all Python dependencies (`uv sync --all-extras`)
3. ⚙️ Configures all 5 agents with AgentCore CLI (creates `.bedrock_agentcore.yaml`)
4. 🐳 Creates ECR repositories for all agents
5. 🔐 Sets up OAuth providers (GitHub and JIRA)
6. 🚀 Deploys all agents to AWS (optional)

**Note:** `.bedrock_agentcore.yaml` is gitignored, so Step 3 is required for new clones.

**Environment Setup:**
- Creates `.env` from `.env.example` if not exists
- Prompts you to add credentials before continuing
- Required variables:
  - `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` (for GitHub agent)
  - `ATLASSIAN_CLIENT_ID` / `ATLASSIAN_CLIENT_SECRET` (for JIRA agent)
  - `JIRA_URL` (for JIRA agent)

**Time Estimate:**
- Configuration: ~2 minutes
- Deployment (if enabled): ~60-75 minutes (5 agents × 12-15 min each)

**Output:**
- Colored progress indicators (✅ success, ⚠️ warnings, ❌ errors)
- Clear next steps for testing
- Agent ARNs and deployment status

**Skipping Steps:**
You can skip deployment and run it manually later:
```bash
# Script will ask: "Deploy all agents now? (y/n)"
# Answer 'n' to skip, then deploy manually:
uv run poe deploy-github
uv run poe deploy-planning
uv run poe deploy-jira
uv run poe deploy-coding
uv run poe deploy-orchestrator
```

**Troubleshooting:**

*Credentials expired during deployment:*
```bash
# Re-authenticate
authenticate --to=wealth-dev-au
# Continue with failed agent
uv run poe deploy-<agent-name>
```

*Missing OAuth credentials:*
```bash
# Setup GitHub provider separately
python setup_github_provider.py

# Setup JIRA provider separately
python setup_jira_provider.py
```

*ECR repository already exists:*
- Script will skip and continue (safe to re-run)

## Manual Setup

If you prefer manual control, follow the commands in:
- `docs/AWS-AgentCore-Setup.md` - Complete step-by-step guide
- `QUICK_REFERENCE.md` - All commands in copy-paste format

## Testing After Setup

```bash
# Planning Agent (no OAuth)
uv run poe invoke-planning '{"prompt": "Hello"}' --user-id "test"

# GitHub Agent (OAuth on first use)
uv run poe invoke-github '{"prompt": "list my repositories"}' --user-id "test"

# JIRA Agent (OAuth on first use)
uv run poe invoke-jira '{"prompt": "Get details for PROJ-123"}' --user-id "test"

# Coding Agent
uv run poe invoke-coding '{"prompt": "Setup a new workspace"}' --user-id "test"

# Orchestrator Agent
uv run poe invoke-orchestrator '{"prompt": "Parse this: Fix bug"}' --user-id "test"
```

**Important:** The `--user-id` parameter is **required** for OAuth agents (GitHub, JIRA).

## Region Configuration

All scripts use `ap-southeast-2` (Sydney) by default.

Override with environment variable:
```bash
export AWS_REGION=ap-southeast-2
./scripts/setup-new-aws-account.sh
```
