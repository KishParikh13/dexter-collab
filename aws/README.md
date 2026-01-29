# Dexter Dashboard - AWS Backend

Secure AWS backend for Dexter Dashboard task management.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Dashboard      │────▶│  API Gateway     │────▶│  Lambda         │
│  (GitHub Pages) │     │  (REST API)      │     │  (Python 3.11)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                         │
                              ┌───────────────────────────┼───────────────────────────┐
                              │                           │                           │
                              ▼                           ▼                           │
                        ┌───────────┐             ┌─────────────┐                    │
                        │ DynamoDB  │             │ DynamoDB    │                    │
                        │ Tasks     │             │ Sessions    │                    │
                        └───────────┘             └─────────────┘                    │
```

## Features

- **DynamoDB Tables:** Serverless, pay-per-request billing
- **Lambda Function:** Single function handles all CRUD operations
- **API Gateway:** REST API with CORS, API key authentication
- **Security:** 
  - API key required for write operations (POST/PUT/DELETE)
  - GET operations public for dashboard read access
  - CORS restricted to https://kishparikh13.github.io
  - IAM roles with least privilege

## Prerequisites

1. AWS CLI configured with credentials
2. SAM CLI installed: `pip install aws-sam-cli`
3. Python 3.11+

## Quick Deploy

```bash
# Navigate to aws directory
cd /data/workspace/dexter-collab/aws

# Make deploy script executable
chmod +x deploy.sh

# Deploy to production
./deploy.sh prod

# Or deploy to dev
./deploy.sh dev
```

## Manual Deploy

```bash
# Validate template
sam validate --template template.yaml

# Build
sam build

# Deploy
sam deploy --guided
```

## API Endpoints

### Tasks

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /tasks | No | List all tasks |
| GET | /tasks/{id} | No | Get single task |
| POST | /tasks | API Key | Create task |
| PUT | /tasks/{id} | API Key | Update task |
| DELETE | /tasks/{id} | API Key | Delete task |

### Sessions

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /sessions | No | List active sessions |
| PUT | /sessions/{id} | API Key | Update session status |

### Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /health | No | Health check |

## Task Schema

```json
{
  "id": "string (UUID)",
  "title": "string (required, max 500)",
  "description": "string (optional, max 5000)",
  "repo": "string (optional, max 200)",
  "status": "backlog | in-progress | review | done",
  "currentStep": "string (current step description)",
  "steps": [
    {
      "name": "string",
      "status": "done | in-progress | pending",
      "detail": "string (optional)"
    }
  ],
  "cost": "number (optional, USD)",
  "timeMs": "number (optional, milliseconds)",
  "createdAt": "ISO 8601 timestamp",
  "updatedAt": "ISO 8601 timestamp",
  "startedAt": "ISO 8601 timestamp (auto-set on in-progress)",
  "completedAt": "ISO 8601 timestamp (auto-set on done)",
  "agentId": "string (optional, agent that worked on task)"
}
```

## Session Schema

```json
{
  "id": "main | agent-id",
  "status": "active | idle",
  "lastActiveAt": "ISO 8601 timestamp",
  "currentAction": "string (what Dexter is doing)",
  "ttl": "unix timestamp (auto-expire after 1 hour)"
}
```

## API Examples

### Create Task

```bash
curl -X POST https://API_ENDPOINT/tasks \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Build login page",
    "description": "Create a login page with email/password",
    "repo": "KishParikh13/my-app",
    "status": "backlog"
  }'
```

### Update Task Status

```bash
curl -X PUT https://API_ENDPOINT/tasks/TASK_ID \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in-progress",
    "currentStep": "Setting up project structure"
  }'
```

### Update Session (Dexter reports status)

```bash
curl -X PUT https://API_ENDPOINT/sessions/main \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "active",
    "currentAction": "Analyzing codebase..."
  }'
```

### List Tasks

```bash
curl https://API_ENDPOINT/tasks

# Filter by status
curl https://API_ENDPOINT/tasks?status=in-progress
```

## Dashboard Configuration

After deployment, update `config.js` in the dashboard:

```javascript
window.DEXTER_CONFIG = {
  apiEndpoint: 'https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod',
  apiKey: 'YOUR_API_KEY',  // Store securely!
  useApi: true
};
```

**Security Note:** Don't commit API keys to public repos. Options:
1. Use environment variables in build process
2. Create `config.local.js` (gitignored)
3. Load from secure backend service

## Cleanup

```bash
# Delete stack and all resources
aws cloudformation delete-stack --stack-name dexter-dashboard-prod

# Or delete dev stack
aws cloudformation delete-stack --stack-name dexter-dashboard-dev
```

## Costs

With PAY_PER_REQUEST billing:
- **DynamoDB:** ~$0.25 per million read requests, $1.25 per million writes
- **Lambda:** First 1M requests/month free, then $0.20 per million
- **API Gateway:** First 1M calls/month free, then $3.50 per million

For typical personal use, expect **< $1/month**.

## Troubleshooting

### CORS Errors
- Verify origin matches exactly: `https://kishparikh13.github.io`
- Check API Gateway stage is deployed after changes

### 403 Forbidden on POST/PUT/DELETE
- Ensure `x-api-key` header is present
- Verify API key is valid and enabled

### Lambda Timeout
- Default is 30s, increase if needed
- Check DynamoDB capacity

### Debug Mode
Enable in config:
```javascript
window.DEXTER_CONFIG.debug = true;
```

## Local Development

```bash
# Start local API
sam local start-api

# Test locally
curl http://127.0.0.1:3000/health
```
