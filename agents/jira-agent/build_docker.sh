#!/bin/bash
set -e

echo "🐳 Building JIRA Agent Docker image..."

# Change to script directory
cd "$(dirname "$0")"

# Build with BuildKit for better caching
DOCKER_BUILDKIT=1 docker build \
  --platform linux/arm64 \
  --tag jira-agent:latest \
  --tag jira-agent:$(date +%Y%m%d-%H%M%S) \
  .

echo "✅ Build complete!"
echo "🏷️  Tagged as: jira-agent:latest"
