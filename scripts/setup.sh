#!/bin/bash
set -e

DEPLOY=${1:-false}

echo "🚀 Multi-Agent Platform Setup"
echo "=============================="
echo ""

# 1. Setup shared AWS resources
echo "Step 1/3: Creating shared AWS resources..."
./scripts/setup_shared_resources.sh

# 2. Configure all agents
echo ""
echo "Step 2/3: Configuring agents..."
./scripts/configure_agents.sh

# 3. Deploy (optional)
if [ "$DEPLOY" = "--deploy" ]; then
  echo ""
  echo "Step 3/3: Deploying all agents..."
  ./scripts/deploy_all.sh
else
  echo ""
  echo "✅ Setup complete!"
  echo ""
  echo "📝 Next steps:"
  echo "   Deploy all: ./scripts/deploy_all.sh"
  echo "   Or deploy one: agentcore launch --agent orchestrator"
fi
