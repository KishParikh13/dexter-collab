#!/bin/bash
# Test Dexter API endpoints
# Usage: ./test-api.sh [API_ENDPOINT] [API_KEY]

API_ENDPOINT="${1:-$(cat config-prod.json 2>/dev/null | grep apiEndpoint | cut -d'"' -f4)}"
API_KEY="${2:-$(cat config-prod.json 2>/dev/null | grep apiKey | cut -d'"' -f4)}"

if [ -z "$API_ENDPOINT" ]; then
    echo "Error: API endpoint not provided"
    echo "Usage: ./test-api.sh API_ENDPOINT API_KEY"
    exit 1
fi

echo "============================================"
echo "Testing Dexter API"
echo "Endpoint: $API_ENDPOINT"
echo "============================================"
echo ""

# Health check
echo "1. Health Check (GET /health)"
echo "---"
curl -s "$API_ENDPOINT/health" | jq .
echo ""

# List tasks
echo "2. List Tasks (GET /tasks)"
echo "---"
curl -s "$API_ENDPOINT/tasks" | jq .
echo ""

# Create test task
echo "3. Create Task (POST /tasks)"
echo "---"
TASK_ID="test-$(date +%s)"
CREATE_RESPONSE=$(curl -s -X POST "$API_ENDPOINT/tasks" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"$TASK_ID\",
    \"title\": \"Test Task - $(date)\",
    \"description\": \"Automated test task\",
    \"status\": \"backlog\"
  }")
echo "$CREATE_RESPONSE" | jq .
echo ""

# Get task
echo "4. Get Task (GET /tasks/$TASK_ID)"
echo "---"
curl -s "$API_ENDPOINT/tasks/$TASK_ID" | jq .
echo ""

# Update task
echo "5. Update Task (PUT /tasks/$TASK_ID)"
echo "---"
curl -s -X PUT "$API_ENDPOINT/tasks/$TASK_ID" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"status": "in-progress", "currentStep": "Testing update"}' | jq .
echo ""

# List sessions
echo "6. List Sessions (GET /sessions)"
echo "---"
curl -s "$API_ENDPOINT/sessions" | jq .
echo ""

# Update session
echo "7. Update Session (PUT /sessions/main)"
echo "---"
curl -s -X PUT "$API_ENDPOINT/sessions/main" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"status": "active", "currentAction": "Running API tests"}' | jq .
echo ""

# Verify session
echo "8. Verify Session (GET /sessions)"
echo "---"
curl -s "$API_ENDPOINT/sessions" | jq .
echo ""

# Delete test task
echo "9. Delete Task (DELETE /tasks/$TASK_ID)"
echo "---"
curl -s -X DELETE "$API_ENDPOINT/tasks/$TASK_ID" \
  -H "x-api-key: $API_KEY" | jq .
echo ""

# Set session to idle
echo "10. Set Session Idle (PUT /sessions/main)"
echo "---"
curl -s -X PUT "$API_ENDPOINT/sessions/main" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"status": "idle"}' | jq .
echo ""

echo "============================================"
echo "Tests Complete!"
echo "============================================"
