# Async Task Pattern

## Overview

Planning Agent supports async task execution to avoid timeouts on long-running operations.

## Two Execution Modes

### Sync Mode (Default)
**When to use**: Simple, quick requests
**Behavior**: Returns result immediately
**Timeout Risk**: Yes (2-minute AgentCore limit)

```bash
aws_use mingfang && uv run poe invoke-planning \
  '{"prompt": "Parse requirements for a todo app"}'

# Response arrives immediately with result
```

### Async Mode (Fire + Poll)
**When to use**: Complex requests, detailed analysis, or user preference
**Behavior**: Returns task_id immediately, poll for results
**Timeout Risk**: No - operations can run as long as needed

```bash
# Submit task (returns immediately with task_id)
aws_use mingfang && uv run poe invoke-planning \
  '{"prompt": "Submit async: Generate comprehensive 10-phase implementation plan with detailed risk analysis"}'

# Response: task_id (e.g., "a1b2c3d4-...")

# Poll for results (can call multiple times)
aws_use mingfang && uv run poe invoke-planning \
  '{"prompt": "Get result for task a1b2c3d4-..."}'

# Response: Status (pending/processing/completed) + result when done
```

## How Agent Chooses Mode

The agent automatically selects the appropriate mode based on:

1. **User keywords**: "async", "submit task", "in background", "fire and forget"
2. **Request complexity**: Detailed/comprehensive plans trigger async
3. **Default**: Simple requests use sync mode

### Example Prompts

**Sync Mode** (automatic):
```
"Parse requirements for todo app"
"Generate 3-phase implementation plan"
"Validate this plan: [plan text]"
```

**Async Mode** (automatic):
```
"Submit async: Create comprehensive enterprise architecture"
"In background, generate detailed implementation plan with risk analysis"
"Fire and forget: Analyze 10 different implementation approaches"
```

**Explicit Async**:
```
"Use async mode to generate plan for authentication system"
```

## Async Tools

### submit_plan_generation(requirement: str)
Submit implementation plan generation task.

**Returns**: Task ID immediately

**Example**:
```python
Input: "Submit async: Plan authentication system"
Agent calls: submit_plan_generation("authentication system")
Output: "Task ID: abc-123. Use get_task_result() to check status"
```

### submit_requirements_parsing(requirements_text: str)
Submit requirements parsing task.

**Returns**: Task ID immediately

### submit_plan_validation(plan_text: str)
Submit plan validation task.

**Returns**: Task ID immediately

### get_task_result(task_id: str)
Poll for task status and retrieve results.

**Returns**:
- **Pending**: Task queued for execution
- **Processing**: Task currently running
- **Completed**: Full result text
- **Failed**: Error message with retry guidance

**Example**:
```python
Input: "Check status of task abc-123"
Agent calls: get_task_result("abc-123")
Output: "✅ Task Completed! Result: [plan text]"
```

## Task Lifecycle

```
1. Submit
   └─> Return task_id immediately (< 1 second)

2. Background Processing
   └─> Task executes in separate thread
   └─> Includes retry logic for throttling
   └─> Updates status: pending → processing → completed/failed

3. Poll for Results
   └─> Call get_task_result(task_id) anytime
   └─> Can poll multiple times until completed
   └─> No timeout risk
```

## Implementation Details

### Task Storage
- **Storage**: In-memory (Python dict)
- **Persistence**: Tasks lost on agent restart
- **Expiry**: Auto-cleanup after 1 hour
- **Production**: Upgrade to DynamoDB for persistence

### Execution
- **Background**: Python threading (daemon threads)
- **Retry**: Same exponential backoff as sync tools
- **Logging**: CloudWatch shows task creation/completion

### Limitations (MVP)
1. **No persistence**: Tasks lost on agent restart
2. **No cross-instance**: Works only within single agent instance
3. **1-hour expiry**: Old tasks auto-deleted
4. **Memory-based**: Not suitable for high-volume production

### Production Upgrades

For production deployment, consider:

**DynamoDB Task Store**:
```python
class DynamoDBTaskStore(TaskStore):
    def __init__(self, table_name):
        self.table = boto3.resource('dynamodb').Table(table_name)

    def create_task(self, tool_name, args):
        task_id = str(uuid.uuid4())
        self.table.put_item(Item={
            'task_id': task_id,
            'status': 'pending',
            'tool_name': tool_name,
            'args': json.dumps(args),
            'created_at': time.time()
        })
        return task_id

    def get_task(self, task_id):
        response = self.table.get_item(Key={'task_id': task_id})
        return response.get('Item')
```

**SQS + Lambda**:
- Submit task → Write to SQS queue
- Lambda processor picks up tasks
- Results written to DynamoDB
- Agent polls DynamoDB for status

**Webhooks** (future):
```python
def submit_task_with_callback(tool_name, args, webhook_url):
    task_id = create_task(tool_name, args, webhook_url)
    # When complete, POST result to webhook_url
    return task_id
```

## Usage Examples

### Example 1: Complex Plan (Async Automatic)

**User**: "Generate a comprehensive 10-phase implementation plan for enterprise authentication system with SSO, MFA, audit logging, and compliance requirements"

**Agent**: Detects complexity, uses async mode automatically

**Flow**:
```
1. Agent: submit_plan_generation(detailed_requirement)
   → Returns: "Task ID: task-xyz-789"

2. User waits 10-30 seconds

3. Agent: get_task_result("task-xyz-789")
   → Returns: Complete implementation plan
```

### Example 2: Simple Request (Sync Automatic)

**User**: "Parse requirements for a todo app"

**Agent**: Simple request, uses sync mode

**Flow**:
```
1. Agent: parse_requirements("todo app")
   → Returns: Parsed requirements immediately
```

### Example 3: Explicit Async

**User**: "Use async mode to generate plan for blog platform"

**Agent**: User explicitly requested async

**Flow**:
```
1. Agent: submit_plan_generation("blog platform")
   → Returns: "Task ID: task-abc-123"

2. User: "Check status"

3. Agent: get_task_result("task-abc-123")
   → Returns: Status (processing/completed)
```

### Example 4: Multi-Task Workflow

**User**: "Submit 3 tasks: parse requirements for A, B, and C"

**Agent**: Submits all 3 tasks

**Flow**:
```
1. submit_requirements_parsing("A") → task-1
2. submit_requirements_parsing("B") → task-2
3. submit_requirements_parsing("C") → task-3

All execute in parallel in background

4. Poll all 3:
   get_task_result("task-1")
   get_task_result("task-2")
   get_task_result("task-3")
```

## Benefits

### vs Sync Mode
✅ **No timeout risk** - operations can run indefinitely
✅ **User freedom** - user can do other things while waiting
✅ **Parallel execution** - submit multiple tasks at once
✅ **Retry handling** - automatic retry with backoff built-in

### vs Callbacks
✅ **Simpler** - no webhook setup needed
✅ **Flexible** - poll whenever ready
✅ **User control** - user decides when to check

### Trade-offs
⚠️ **Polling overhead** - user must actively check status
⚠️ **No persistence** - tasks lost on restart (MVP limitation)
⚠️ **Memory-based** - not suitable for high volume

## Monitoring

### Check Task Status in CloudWatch

```bash
# See task creation
aws logs tail /aws/bedrock-agentcore/runtimes/planning_agent-HOo1EJ7KvE-DEFAULT \
  --log-stream-name-prefix "2025/10/08/[runtime-logs]" \
  --since 5m | grep "📝 Created task"

# See task completion
aws logs tail ... | grep "📊 Task.*completed"
```

### Metrics to Track

1. **Task creation rate**: Tasks/minute
2. **Average completion time**: Seconds per task
3. **Failure rate**: Failed / Total tasks
4. **Cleanup frequency**: Old tasks removed

## Testing

### Test Async Flow

```bash
# 1. Submit task
aws_use mingfang && uv run poe invoke-planning \
  '{"prompt": "Submit async: Generate plan for authentication"}'

# Response contains task_id, e.g., "abc-123"

# 2. Check status immediately (should be processing)
aws_use mingfang && uv run poe invoke-planning \
  '{"prompt": "Get result for task abc-123"}'

# Response: "Task Processing..."

# 3. Wait 10 seconds

# 4. Check again (should be completed)
aws_use mingfang && uv run poe invoke-planning \
  '{"prompt": "Get result for task abc-123"}'

# Response: "Task Completed! Result: [plan text]"
```

### Test Parallel Execution

```bash
# Submit 3 tasks rapidly (no delay)
for i in {1..3}; do
  aws_use mingfang && uv run poe invoke-planning \
    "{\"prompt\": \"Submit async: Parse requirements for app $i\"}"
done

# All 3 execute in parallel with automatic retry
# Check each task_id for results
```

## Summary

| Feature | Sync Mode | Async Mode |
|---------|-----------|------------|
| Response time | Immediate | < 1 second (task_id) |
| Timeout risk | Yes (2 min) | No |
| User experience | Simple | Requires polling |
| Parallel execution | No | Yes |
| Complex operations | Limited | Unlimited |
| Retry logic | ✅ | ✅ |
| Production ready | ✅ | MVP (upgrade for production) |

**Recommendation**:
- **Simple requests**: Use sync mode (automatic)
- **Complex requests**: Use async mode (automatic detection)
- **User preference**: Explicitly request async mode
- **Production**: Upgrade to DynamoDB + SQS for persistence
