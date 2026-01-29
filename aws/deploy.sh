#!/bin/bash
# Dexter Dashboard AWS Backend - Deploy Script
# Usage: ./deploy.sh [dev|prod]

set -e

ENVIRONMENT=${1:-prod}
STACK_NAME="dexter-dashboard-${ENVIRONMENT}"
REGION=${AWS_REGION:-us-east-1}
S3_BUCKET=${SAM_S3_BUCKET:-""}

echo "============================================"
echo "Deploying Dexter Dashboard Backend"
echo "Environment: ${ENVIRONMENT}"
echo "Stack: ${STACK_NAME}"
echo "Region: ${REGION}"
echo "============================================"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI not installed"
    exit 1
fi

# Check SAM CLI
if ! command -v sam &> /dev/null; then
    echo "Error: SAM CLI not installed"
    echo "Install: pip install aws-sam-cli"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS credentials not configured"
    echo "Run: aws configure"
    exit 1
fi

# Navigate to aws directory
cd "$(dirname "$0")"

# Validate template
echo ""
echo "Validating template..."
sam validate --template template.yaml

# Build
echo ""
echo "Building Lambda function..."
sam build --template template.yaml

# Deploy
echo ""
echo "Deploying stack..."

# Use guided deploy if no S3 bucket configured
if [ -z "$S3_BUCKET" ]; then
    sam deploy \
        --stack-name "$STACK_NAME" \
        --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
        --region "$REGION" \
        --parameter-overrides "Environment=${ENVIRONMENT}" \
        --resolve-s3 \
        --no-confirm-changeset
else
    sam deploy \
        --stack-name "$STACK_NAME" \
        --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
        --region "$REGION" \
        --s3-bucket "$S3_BUCKET" \
        --parameter-overrides "Environment=${ENVIRONMENT}" \
        --no-confirm-changeset
fi

# Get outputs
echo ""
echo "============================================"
echo "Deployment Complete!"
echo "============================================"
echo ""

# Get API endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text)

echo "API Endpoint: ${API_ENDPOINT}"

# Get API Key ID and value
API_KEY_ID=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiKeyId`].OutputValue' \
    --output text)

API_KEY_VALUE=$(aws apigateway get-api-key \
    --api-key "$API_KEY_ID" \
    --include-value \
    --region "$REGION" \
    --query 'value' \
    --output text)

echo "API Key: ${API_KEY_VALUE}"
echo ""
echo "Save these values! The API key is needed for write operations."
echo ""

# Test health endpoint
echo "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s "${API_ENDPOINT}/health")
echo "Health check: ${HEALTH_RESPONSE}"
echo ""

# Save config for local use
CONFIG_FILE="config-${ENVIRONMENT}.json"
cat > "$CONFIG_FILE" << EOF
{
  "apiEndpoint": "${API_ENDPOINT}",
  "apiKey": "${API_KEY_VALUE}",
  "environment": "${ENVIRONMENT}",
  "region": "${REGION}",
  "stackName": "${STACK_NAME}",
  "deployedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo "Config saved to: ${CONFIG_FILE}"
echo ""
echo "============================================"
echo "Next Steps:"
echo "============================================"
echo "1. Add API endpoint to dashboard config"
echo "2. Store API key securely (not in public repo)"
echo "3. Test API endpoints manually:"
echo ""
echo "   # List tasks"
echo "   curl ${API_ENDPOINT}/tasks"
echo ""
echo "   # Create task (requires API key)"
echo "   curl -X POST ${API_ENDPOINT}/tasks \\"
echo "     -H 'x-api-key: ${API_KEY_VALUE}' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"title\": \"Test task\", \"status\": \"backlog\"}'"
echo ""
echo "   # Update task"
echo "   curl -X PUT ${API_ENDPOINT}/tasks/{id} \\"
echo "     -H 'x-api-key: ${API_KEY_VALUE}' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"status\": \"in-progress\"}'"
echo ""
