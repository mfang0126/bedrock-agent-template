# Timeout Handling Strategy

## Overview

This document describes timeout handling strategies for the multi-agent platform.

## 1. Bedrock API Throttling (Planning Agent)

### Problem
Planning Agent tools make direct calls to Bedrock Converse API, which has rate limits:
- Error: `ThrottlingException: Too many requests, please wait before trying again`
- Happens during rapid consecutive requests
- Default boto3 retry logic insufficient

### Solution: Exponential Backoff Retry

Implemented in `src/tools/planning/plan_generator.py`:

```python
def call_bedrock_with_retry(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 4000,
    temperature: float = 0.7,
    max_retries: int = 3
) -> str:
    """Call Bedrock with exponential backoff retry."""

    for attempt in range(max_retries):
        try:
            response = bedrock_runtime.converse(...)
            return response['output']['message']['content'][0]['text']

        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                if attempt < max_retries - 1:
                    wait_time = 2 ** (attempt + 1)  # 2s, 4s, 8s
                    print(f"⏳ Throttled. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception("Max retries exceeded. Wait 30s before trying again.")
            else:
                raise  # Non-throttling errors fail immediately
```

### Retry Strategy

**Exponential Backoff**:
- Attempt 1: Immediate
- Attempt 2: Wait 2 seconds
- Attempt 3: Wait 4 seconds
- Attempt 4: Wait 8 seconds

**Why This Works**:
- Gives Bedrock time to free up capacity
- Exponential increase prevents thundering herd
- Max 3 retries keeps total wait reasonable (~14 seconds max)

### Usage

All Planning Agent tools automatically use retry logic:
- `generate_implementation_plan()`
- `parse_requirements()`
- `validate_plan()`

No code changes needed for tool consumers.

## 2. AgentCore Invoke Timeout

### Problem
AgentCore invoke operations timeout after 2 minutes:
- Affects long-running LLM operations
- Planning Agent tool chains can exceed limit
- Error: `Command timed out after 2m 0s`

### Solutions

#### Option A: Reduce Request Scope
**Best for**: Interactive usage, user-facing invocations

```bash
# Bad - too complex, may timeout
"Create a comprehensive 10-phase implementation plan with detailed risk analysis and resource estimates"

# Good - scoped request
"Generate a 3-phase implementation plan for user authentication"
```

#### Option B: Streaming Responses (Future Enhancement)
**Best for**: Long-running operations

```python
# Future implementation with streaming
@app.entrypoint
async def strands_agent_planning(payload):
    # Stream partial results as they're generated
    async for chunk in agent.stream(user_input):
        yield {"result": {"partial": chunk}}

    yield {"result": {"complete": True}}
```

#### Option C: Async Task Pattern (Future Enhancement)
**Best for**: Background processing

```python
# Submit task and poll for results
task_id = await agent.submit_task(user_input)
# User can poll: GET /tasks/{task_id}
```

### Current Recommendations

**For Planning Agent**:
1. Keep requests focused and scoped
2. Use specific, actionable prompts
3. Avoid requesting multiple operations in single call
4. Break complex plans into phases

**Examples**:

✅ **Good Requests**:
- "Parse requirements for a todo app"
- "Generate implementation plan for login feature"
- "Validate this 3-phase deployment plan"

❌ **Requests That May Timeout**:
- "Create a comprehensive enterprise architecture with security, scaling, monitoring, deployment, and disaster recovery plans"
- "Generate 10 different implementation approaches and compare them"

## 3. GitHub Agent Timeout (OAuth)

### Problem
First-time OAuth flow requires user authorization, which can timeout if user doesn't respond quickly.

### Solution
OAuth URL returned immediately without timeout:

```python
# Check if OAuth URL was generated
if pending_oauth_url:
    return {
        "result": {
            "role": "assistant",
            "content": [{"text": f"Visit: {pending_oauth_url}"}]
        }
    }
```

**Flow**:
1. User invokes agent
2. Agent immediately returns OAuth URL (no timeout)
3. User authorizes in browser
4. User invokes agent again with cached token
5. Agent proceeds with GitHub operations

## 4. Monitoring and Debugging

### CloudWatch Logs

**Check for throttling**:
```bash
aws_use mingfang && uv run aws logs tail \
  /aws/bedrock-agentcore/runtimes/planning_agent-HOo1EJ7KvE-DEFAULT \
  --log-stream-name-prefix "2025/10/08/[runtime-logs]" \
  --since 5m | grep "Throttl"
```

**Monitor retry behavior**:
```bash
# Look for retry messages
aws logs tail ... | grep "⏳ Throttled"
```

### Metrics to Track

1. **Bedrock API calls per minute**
2. **Retry success rate**
3. **Average response time**
4. **Timeout frequency**

## 5. Rate Limit Best Practices

### For Developers

**Test throttling behavior**:
```python
# Test script to verify retry logic
for i in range(10):
    result = generate_implementation_plan("test feature")
    print(f"Request {i+1}: {result[:50]}...")
    time.sleep(1)  # Add delay between requests
```

**Add delays between consecutive calls**:
```python
# In agent code
result1 = tool1()
time.sleep(2)  # Give Bedrock breathing room
result2 = tool2()
```

### For Users

**Avoid rapid fire requests**:
- Wait 3-5 seconds between Planning Agent invocations
- First request after idle period is always fast
- Subsequent requests benefit from retry logic

## 6. Future Enhancements

### Planned Improvements

1. **Request Queuing**: Queue requests during throttling instead of failing
2. **Token Bucket Algorithm**: More sophisticated rate limiting
3. **Response Caching**: Cache common planning patterns
4. **Streaming Support**: Long operations stream partial results
5. **Async Task API**: Submit tasks and poll for completion

### Configuration Options (Future)

```yaml
# .bedrock_agentcore.yaml
planning_agent:
  timeout_config:
    bedrock_retry_max: 5
    bedrock_backoff_base: 2
    invoke_timeout_seconds: 180
    enable_streaming: true
```

## Summary

| Timeout Type | Solution | Status |
|--------------|----------|--------|
| Bedrock Throttling | Exponential backoff retry | ✅ Implemented |
| AgentCore Invoke | Scope requests appropriately | ✅ Best practice |
| OAuth First-Time | Immediate URL return | ✅ Implemented |
| Long Operations | Streaming (future) | 📋 Planned |

**Current Behavior**:
- Planning Agent: Automatic retry with exponential backoff
- GitHub Agent: OAuth URL returned immediately
- Both agents: 2-minute invoke timeout (AgentCore limit)

**Best Practices**:
- Keep requests scoped and specific
- Add delays between rapid requests
- Monitor CloudWatch for throttling patterns
- Use retry logic for all Bedrock calls
