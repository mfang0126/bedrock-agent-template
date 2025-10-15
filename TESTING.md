# Agent Testing Guide

## Summary

We now have **two ways** to test agents:

### 1. Local Testing (Fast, No AWS)
Use `test_*_local.py` scripts to test agents locally with mock authentication.

### 2. AWS Testing (Real OAuth, API Integration)
Use `invoke_*.sh` scripts to test deployed agents in AWS.

---

## Quick Start

### 🚀 Using Make (Easiest)
```bash
# Local testing
make test-coding
make test-github
make test-jira
make test-all

# AWS testing (requires deployment)
make invoke-coding
make invoke-github
make invoke-jira

# View all commands
make help
```

### 📝 Direct Commands

#### Local Testing
```bash
# From project root
uv run scripts/test_coding_local.py 'what can you do'
uv run scripts/test_github_local.py 'what can you do'
uv run scripts/test_jira_local.py 'what can you do'
```

#### AWS Testing
```bash
# From scripts/ directory
cd scripts/
./invoke_coding.sh 'what can you do'
./invoke_github.sh 'list my repositories'
./invoke_jira.sh 'show my projects'
```

---

## What Was Fixed

### Problem
The `invoke_*.sh` scripts were moved to `scripts/` folder but still had paths assuming they were in the project root.

### Solution
1. **Fixed path**: Changed `AGENT_DIR="${SCRIPT_DIR}/agents/..."` to `AGENT_DIR="${SCRIPT_DIR}/../agents/..."`
2. **Created local test scripts**: New `test_*_local.py` scripts for testing without AWS
3. **Clarified documentation**: Updated all scripts to explain local vs AWS testing

---

## Files Changed

### Invoke Scripts (AWS Testing)
- `invoke_coding.sh` - Fixed path + added local testing instructions
- `invoke_github.sh` - Fixed path + added local testing instructions
- `invoke_jira.sh` - Fixed path + added local testing instructions
- `invoke_orchestrator.sh` - Fixed path
- `invoke_planning.sh` - Fixed path

### New Local Test Scripts
- `test_coding_local.py` - Test Coding agent locally
- `test_github_local.py` - Test GitHub agent with mock auth
- `test_jira_local.py` - Test JIRA agent with mock auth

### Documentation
- `scripts/README.md` - Added "Testing Agents" section

---

## Key Differences

| Aspect | Local Testing | AWS Testing |
|--------|--------------|-------------|
| **AWS Required** | ❌ No | ✅ Yes |
| **OAuth Setup** | ❌ No (mock) | ✅ Yes (real) |
| **API Calls** | ❌ Fail (mock tokens) | ✅ Work (real tokens) |
| **Iteration Speed** | ⚡ Fast | 🐢 Slower |
| **Use Case** | Agent logic/structure | Real integration |

---

## When to Use Which

### Use Local Testing (`test_*_local.py`) when:
- Developing agent logic
- Testing tool configurations
- Debugging agent structure
- Fast iteration needed
- No AWS access available

### Use AWS Testing (`invoke_*.sh`) when:
- Testing OAuth flows
- Validating API integrations
- End-to-end testing
- Production validation
- Real data needed

---

## Common Issues

### "No module named 'strands'"
**Solution:** Use `uv run` to run the test scripts:
```bash
uv run scripts/test_coding_local.py 'prompt'
```

### "cd: No such file or directory"
**Solution:** Already fixed! Path now uses `../agents/` correctly.

### "OAuth error" with local testing
**Expected:** Local testing uses mock auth, so OAuth flows won't work. This is normal.

---

## Next Steps

1. **Try local testing:**
   ```bash
   make test-coding
   # or
   uv run scripts/test_coding_local.py 'what can you do'
   ```

2. **Deploy agents to AWS:** (if not already deployed)
   ```bash
   make setup
   make deploy
   # or
   cd scripts/
   ./setup.sh --deploy
   ```

3. **Test deployed agents:**
   ```bash
   make invoke-coding
   # or
   cd scripts/
   ./invoke_coding.sh 'what can you do'
   ```

## Makefile Commands

Run `make help` to see all available commands:

```bash
make help           # Show all commands
make test-all       # Test all agents locally
make test-coding    # Test Coding agent
make test-github    # Test GitHub agent (mock)
make test-jira      # Test JIRA agent (mock)
make invoke-coding  # Test deployed Coding agent
make invoke-github  # Test deployed GitHub agent
make invoke-jira    # Test deployed JIRA agent
make setup          # Setup AWS resources
make deploy         # Deploy all agents
make deploy-agent A=coding  # Deploy specific agent
make status         # Show agent status
make clean          # Clean temporary files
```

---

## Architecture

```
scripts/
├── invoke_*.sh           # AWS deployment testing
├── test_*_local.py       # Local mock testing
├── setup*.sh             # Deployment scripts
└── README.md             # Full documentation

agents/
├── coding-agent/
├── github-agent/
├── jira-agent/
├── orchestrator-agent/
└── planning-agent/
```

All paths now correctly navigate from `scripts/` to `../agents/`.
