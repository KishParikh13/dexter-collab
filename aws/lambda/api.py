"""
Dexter Dashboard API - Lambda Handler
CRUD operations for tasks and sessions
"""

import json
import os
import uuid
import time
from datetime import datetime, timezone
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
tasks_table = dynamodb.Table(os.environ.get('TASKS_TABLE', 'dexter-tasks-prod'))
sessions_table = dynamodb.Table(os.environ.get('SESSIONS_TABLE', 'dexter-sessions-prod'))
def cors_headers():
    """Return CORS headers for all responses"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Api-Key,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Content-Type': 'application/json'
    }


def response(status_code, body):
    """Create API Gateway response with CORS headers"""
    return {
        'statusCode': status_code,
        'headers': cors_headers(),
        'body': json.dumps(body, default=decimal_serializer)
    }


def decimal_serializer(obj):
    """Handle Decimal serialization for DynamoDB"""
    if isinstance(obj, Decimal):
        return float(obj) if obj % 1 else int(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def validate_task(task_data):
    """Validate task input data"""
    errors = []
    
    # Required fields
    if not task_data.get('title'):
        errors.append('title is required')
    elif len(task_data['title']) > 500:
        errors.append('title must be 500 characters or less')
    
    # Optional field validation
    if task_data.get('status') and task_data['status'] not in ['backlog', 'in-progress', 'review', 'done']:
        errors.append('status must be one of: backlog, in-progress, review, done')
    
    if task_data.get('description') and len(task_data['description']) > 5000:
        errors.append('description must be 5000 characters or less')
    
    if task_data.get('repo') and len(task_data['repo']) > 200:
        errors.append('repo must be 200 characters or less')
    
    return errors


def validate_session(session_data):
    """Validate session input data"""
    errors = []
    
    if session_data.get('status') and session_data['status'] not in ['active', 'idle']:
        errors.append('status must be one of: active, idle')
    
    if session_data.get('currentAction') and len(session_data['currentAction']) > 500:
        errors.append('currentAction must be 500 characters or less')
    
    return errors


def now_iso():
    """Return current time in ISO format"""
    return datetime.now(timezone.utc).isoformat()


# ============================================
# Task Handlers
# ============================================

def get_tasks(event):
    """GET /tasks - List all tasks"""
    try:
        # Optional filtering by status
        params = event.get('queryStringParameters') or {}
        status = params.get('status')
        
        if status:
            # Use GSI for status filtering
            result = tasks_table.query(
                IndexName='status-createdAt-index',
                KeyConditionExpression=Key('status').eq(status),
                ScanIndexForward=False  # Most recent first
            )
        else:
            # Scan all tasks
            result = tasks_table.scan()
        
        tasks = result.get('Items', [])
        
        # Sort by createdAt descending if not using GSI
        if not status:
            tasks.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
        
        return response(200, {'tasks': tasks, 'count': len(tasks)})
    
    except Exception as e:
        print(f"Error getting tasks: {e}")
        return response(500, {'error': 'Failed to retrieve tasks'})


def get_task(event, task_id):
    """GET /tasks/{id} - Get single task"""
    try:
        result = tasks_table.get_item(Key={'id': task_id})
        task = result.get('Item')
        
        if not task:
            return response(404, {'error': 'Task not found'})
        
        return response(200, {'task': task})
    
    except Exception as e:
        print(f"Error getting task: {e}")
        return response(500, {'error': 'Failed to retrieve task'})


def create_task(event):
    """POST /tasks - Create new task"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        # Validate input
        errors = validate_task(body)
        if errors:
            return response(400, {'errors': errors})
        
        # Create task object
        task = {
            'id': body.get('id') or str(uuid.uuid4()),
            'title': body['title'].strip(),
            'description': body.get('description', '').strip(),
            'repo': body.get('repo', '').strip(),
            'status': body.get('status', 'backlog'),
            'currentStep': body.get('currentStep'),
            'steps': body.get('steps', []),
            'cost': Decimal(str(body.get('cost', 0))) if body.get('cost') else None,
            'timeMs': body.get('timeMs'),
            'createdAt': body.get('createdAt') or now_iso(),
            'updatedAt': now_iso(),
            'startedAt': body.get('startedAt'),
            'completedAt': body.get('completedAt'),
            'agentId': body.get('agentId')
        }
        
        # Remove None values
        task = {k: v for k, v in task.items() if v is not None}
        
        # Write to DynamoDB
        tasks_table.put_item(Item=task)
        
        return response(201, {'task': task, 'message': 'Task created successfully'})
    
    except json.JSONDecodeError:
        return response(400, {'error': 'Invalid JSON body'})
    except Exception as e:
        print(f"Error creating task: {e}")
        return response(500, {'error': 'Failed to create task'})


def update_task(event, task_id):
    """PUT /tasks/{id} - Update task"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        # Check task exists
        result = tasks_table.get_item(Key={'id': task_id})
        if not result.get('Item'):
            return response(404, {'error': 'Task not found'})
        
        # Validate input
        errors = validate_task({**result['Item'], **body})
        if errors:
            return response(400, {'errors': errors})
        
        # Build update expression
        update_parts = []
        expression_values = {}
        expression_names = {}
        
        allowed_fields = ['title', 'description', 'repo', 'status', 'currentStep', 
                          'steps', 'cost', 'tokenUsage', 'timeMs', 'startedAt', 'completedAt', 'agentId', 'prUrl', 'context']
        
        for field in allowed_fields:
            if field in body:
                safe_name = f'#{field}'
                safe_value = f':{field}'
                update_parts.append(f'{safe_name} = {safe_value}')
                expression_names[safe_name] = field
                
                # Handle decimal conversion for cost
                if field == 'cost' and body[field] is not None:
                    expression_values[safe_value] = Decimal(str(body[field]))
                else:
                    expression_values[safe_value] = body[field]
        
        # Always update updatedAt
        update_parts.append('#updatedAt = :updatedAt')
        expression_names['#updatedAt'] = 'updatedAt'
        expression_values[':updatedAt'] = now_iso()
        
        # Auto-set timestamps based on status changes
        new_status = body.get('status')
        current_status = result['Item'].get('status')
        
        if new_status == 'in-progress' and current_status != 'in-progress':
            if 'startedAt' not in body:
                update_parts.append('#startedAt = :startedAt')
                expression_names['#startedAt'] = 'startedAt'
                expression_values[':startedAt'] = now_iso()
        
        if new_status == 'done' and current_status != 'done':
            if 'completedAt' not in body:
                update_parts.append('#completedAt = :completedAt')
                expression_names['#completedAt'] = 'completedAt'
                expression_values[':completedAt'] = now_iso()
        
        # Execute update
        result = tasks_table.update_item(
            Key={'id': task_id},
            UpdateExpression='SET ' + ', '.join(update_parts),
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values,
            ReturnValues='ALL_NEW'
        )
        
        return response(200, {'task': result['Attributes'], 'message': 'Task updated successfully'})
    
    except json.JSONDecodeError:
        return response(400, {'error': 'Invalid JSON body'})
    except Exception as e:
        print(f"Error updating task: {e}")
        return response(500, {'error': 'Failed to update task'})


def delete_task(event, task_id):
    """DELETE /tasks/{id} - Delete task"""
    try:
        # Check task exists
        result = tasks_table.get_item(Key={'id': task_id})
        if not result.get('Item'):
            return response(404, {'error': 'Task not found'})
        
        # Delete task
        tasks_table.delete_item(Key={'id': task_id})
        
        return response(200, {'message': 'Task deleted successfully', 'id': task_id})
    
    except Exception as e:
        print(f"Error deleting task: {e}")
        return response(500, {'error': 'Failed to delete task'})


# ============================================
# Session Handlers
# ============================================

def get_sessions(event):
    """GET /sessions - List all active sessions"""
    try:
        result = sessions_table.scan()
        sessions = result.get('Items', [])
        
        # Filter out expired sessions (TTL may not have cleaned up yet)
        current_time = int(time.time())
        sessions = [s for s in sessions if s.get('ttl', current_time + 1) > current_time]
        
        return response(200, {'sessions': sessions, 'count': len(sessions)})
    
    except Exception as e:
        print(f"Error getting sessions: {e}")
        return response(500, {'error': 'Failed to retrieve sessions'})


def update_session(event, session_id):
    """PUT /sessions/{id} - Update or create session"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        # Validate input
        errors = validate_session(body)
        if errors:
            return response(400, {'errors': errors})
        
        # Build session object
        session = {
            'id': session_id,
            'status': body.get('status', 'active'),
            'lastActiveAt': now_iso(),
            'currentAction': body.get('currentAction'),
            # TTL: expire sessions after 1 hour of no updates
            'ttl': int(time.time()) + 3600
        }
        
        # Remove None values
        session = {k: v for k, v in session.items() if v is not None}
        
        # Upsert session
        sessions_table.put_item(Item=session)
        
        return response(200, {'session': session, 'message': 'Session updated successfully'})
    
    except json.JSONDecodeError:
        return response(400, {'error': 'Invalid JSON body'})
    except Exception as e:
        print(f"Error updating session: {e}")
        return response(500, {'error': 'Failed to update session'})


# ============================================
# Health Check
# ============================================

def health_check(event):
    """GET /health - Health check endpoint"""
    return response(200, {
        'status': 'healthy',
        'timestamp': now_iso(),
        'service': 'dexter-api'
    })


# ============================================
# Main Handler
# ============================================

def handler(event, context):
    """Main Lambda handler - routes requests to appropriate handlers"""
    
    # Handle OPTIONS preflight requests
    if event.get('httpMethod') == 'OPTIONS':
        return response(200, {'message': 'OK'})
    
    path = event.get('path', '')
    method = event.get('httpMethod', '')
    path_params = event.get('pathParameters') or {}
    
    print(f"Request: {method} {path}")
    
    # Route requests
    try:
        # Health check
        if path == '/health' and method == 'GET':
            return health_check(event)
        
        # Tasks routes
        if path == '/tasks':
            if method == 'GET':
                return get_tasks(event)
            elif method == 'POST':
                return create_task(event)
        
        if path.startswith('/tasks/') and path_params.get('id'):
            task_id = path_params['id']
            if method == 'GET':
                return get_task(event, task_id)
            elif method == 'PUT':
                return update_task(event, task_id)
            elif method == 'DELETE':
                return delete_task(event, task_id)
        
        # Sessions routes
        if path == '/sessions' and method == 'GET':
            return get_sessions(event)
        
        if path.startswith('/sessions/') and path_params.get('id'):
            session_id = path_params['id']
            if method == 'PUT':
                return update_session(event, session_id)
        
        # No matching route
        return response(404, {'error': 'Not found', 'path': path, 'method': method})
    
    except Exception as e:
        print(f"Unhandled error: {e}")
        return response(500, {'error': 'Internal server error'})
