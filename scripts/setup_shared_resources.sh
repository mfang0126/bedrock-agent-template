#!/bin/bash
set -e

REGION="${AWS_REGION:-ap-southeast-2}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROLE_NAME="AgentCoreSharedExecutionRole"
ECR_REPO="agentcore-agents"
MEMORY_NAME="shared_agent_memory"
STATE_FILE=".aws_resources_state"

echo "🚀 Setting up shared resources for AgentCore agents..."
echo "Region: $REGION"
echo "Account: $ACCOUNT_ID"

# Load existing state if available
if [ -f "$STATE_FILE" ]; then
  source "$STATE_FILE"
  echo "📂 Loaded existing state"
fi

# 1. Create shared execution role
echo ""
echo "📋 Creating shared execution role: $ROLE_NAME"

if [ -n "$SHARED_EXECUTION_ROLE_ARN" ]; then
  echo "✅ Role exists (from state): $SHARED_EXECUTION_ROLE_ARN"
  ROLE_ARN="$SHARED_EXECUTION_ROLE_ARN"
else
  ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text 2>/dev/null || echo "")
  
  if [ -z "$ROLE_ARN" ]; then
  cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

  ROLE_ARN=$(aws iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document file:///tmp/trust-policy.json \
    --query 'Role.Arn' \
    --output text)
  
  # Attach required policies
  aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
  
  aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
  
    echo "✅ Created role: $ROLE_ARN"
  else
    echo "✅ Role exists: $ROLE_ARN"
  fi
  
  # Save to state
  echo "SHARED_EXECUTION_ROLE_ARN=$ROLE_ARN" >> "$STATE_FILE"
fi

# 2. Create shared ECR repository
echo ""
echo "🐳 Creating shared ECR repository: $ECR_REPO"

if [ -n "$SHARED_ECR_REPOSITORY" ]; then
  echo "✅ ECR exists (from state): $SHARED_ECR_REPOSITORY"
else
  ECR_URI=$(aws ecr describe-repositories --repository-names "$ECR_REPO" --region "$REGION" --query 'repositories[0].repositoryUri' --output text 2>/dev/null || echo "")
  
  if [ -z "$ECR_URI" ]; then
    ECR_URI=$(aws ecr create-repository \
      --repository-name "$ECR_REPO" \
      --region "$REGION" \
      --query 'repository.repositoryUri' \
      --output text)
    echo "✅ Created ECR: $ECR_URI"
  else
    echo "✅ ECR exists: $ECR_URI"
  fi
  
  # Save to state
  echo "SHARED_ECR_REPOSITORY=$ECR_REPO" >> "$STATE_FILE"
fi

# 3. Create shared memory
echo ""
echo "🧠 Creating shared memory: $MEMORY_NAME"

if [ -n "$SHARED_MEMORY_ID" ] && [ "$SHARED_MEMORY_ID" != "None" ]; then
  echo "✅ Memory exists (from state): $SHARED_MEMORY_ID"
  MEMORY_ID="$SHARED_MEMORY_ID"
else
  # Check if memory already exists
  echo "Checking for existing memory..."
  MEMORY_ID=$(aws bedrock-agentcore-control list-memories --region "$REGION" --query "memories[?starts_with(id, '$MEMORY_NAME')].id" --output text 2>/dev/null || echo "")
  
  if [ -z "$MEMORY_ID" ]; then
    # Create new memory
    echo "Creating memory: $MEMORY_NAME"
    MEMORY_ID=$(aws bedrock-agentcore-control create-memory \
      --name "$MEMORY_NAME" \
      --memory-execution-role-arn "$ROLE_ARN" \
      --event-expiry-duration 30 \
      --region "$REGION" \
      --query 'memory.id' \
      --output text 2>&1)
    
    if [ -n "$MEMORY_ID" ] && [[ ! "$MEMORY_ID" =~ "error" ]] && [[ ! "$MEMORY_ID" =~ "Error" ]]; then
      echo "✅ Created memory: $MEMORY_ID"
    else
      echo "❌ Failed to create memory: $MEMORY_ID"
      exit 1
    fi
  else
    echo "✅ Memory exists: $MEMORY_ID"
  fi
  
  # Save to state
  echo "SHARED_MEMORY_ID=$MEMORY_ID" >> "$STATE_FILE"
fi

# 4. Export for next script
echo ""
echo "💾 Exporting shared resources..."
export SHARED_EXECUTION_ROLE_ARN="$ROLE_ARN"
export SHARED_ECR_REPOSITORY="$ECR_REPO"
export SHARED_MEMORY_ID="$MEMORY_ID"

# Save to .env (update or append)
if grep -q "SHARED_EXECUTION_ROLE_ARN" .env 2>/dev/null; then
  sed -i.bak "s|SHARED_EXECUTION_ROLE_ARN=.*|SHARED_EXECUTION_ROLE_ARN=$ROLE_ARN|" .env
  sed -i.bak "s|SHARED_ECR_REPOSITORY=.*|SHARED_ECR_REPOSITORY=$ECR_REPO|" .env
  sed -i.bak "s|SHARED_MEMORY_ID=.*|SHARED_MEMORY_ID=$MEMORY_ID|" .env
  rm -f .env.bak
else
  cat >> .env <<EOF

# Shared Resources (auto-generated)
SHARED_EXECUTION_ROLE_ARN=$ROLE_ARN
SHARED_ECR_REPOSITORY=$ECR_REPO
SHARED_MEMORY_ID=$MEMORY_ID
EOF
fi

echo "✅ Shared resources ready!"
echo "📂 State saved to: $STATE_FILE and .env"
