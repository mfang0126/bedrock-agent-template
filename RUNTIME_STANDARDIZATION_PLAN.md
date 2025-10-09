# Runtime Standardization Plan

## Overview
Standardize all agent runtime files to use consistent patterns for streaming responses, response formatting, error handling, and AgentCore integration.

## Current State Analysis

### ✅ Planning Agent (Simplified Runtime in Place)
- **Streaming**: ⚠️ Returns a single formatted payload (streaming optional)
- **Response Formatter**: ✅ Uses `format_planning_response` for final payload
- **Structure**: ✅ Minimal AgentCore entrypoint without Bedrock dependency
- **Error Handling**: ✅ Shared `create_error_response()` for failures

### ❌ JIRA Agent (Needs Major Updates)
- **Streaming**: ❌ Uses synchronous `agent(user_input)`
- **Response Formatter**: ✅ Module exists but runtime does not consume it
- **Structure**: ✅ Async entrypoint exists but returns sync payloads
- **Error Handling**: ⚠️ Manual dictionary construction

### ❌ GitHub Agent (Needs Major Updates)
- **Streaming**: ❌ Uses synchronous `agent(user_input)`
- **Response Formatter**: ✅ Module exists but runtime does not consume it
- **Structure**: ✅ Async entrypoint scaffold present
- **Error Handling**: ⚠️ Manual dictionary construction

### ⚠️ Coding Agent (Partial Rewrite Complete)
- **Streaming**: ❌ Runtime still missing Agent stream wrapper
- **Response Formatter**: ✅ Module aligned with coding workflow
- **Structure**: ⚠️ Runtime returns Agent instance; no AgentCore entrypoint
- **Error Handling**: ⚠️ Workspace tooling now captures command errors, runtime still logging only

## Standardization Goals

### 1. Unified Runtime Pattern
All agents should follow this structure:
```
1. Import response formatter
2. Create AgentCore app
3. Configure model and agent
4. Define async entrypoint with streaming
5. Use response formatter for all outputs
6. Handle errors consistently
```

### 2. Streaming Support
All agents must support async streaming:
- Use `agent.stream_async(user_input)`
- Yield streaming events properly
- Handle streaming errors gracefully

### 3. Response Formatter Integration
All agents must use their response formatters:
- Import and use the existing module in each runtime
- Standardize response structures emitted during streaming
- Use formatter helpers for both success and error responses

### 4. Error Handling Consistency
All agents should handle errors the same way:
- Use response formatter for error responses
- Log errors with proper context
- Return user-friendly error messages
- Maintain streaming during errors

## Implementation Sequence

### Phase 1: Response Formatter Alignment ✅ Completed
**Targets**: Planning, GitHub, JIRA, Coding  
**Highlights**:
1. Ensured every agent owns `common/response_formatter.py`
2. Trimmed helper functions to agent-specific needs
3. Synced docs (`docs/clean_json_functions.md`, `docs/coding_agent_setup.md`) with new module names

**Remaining follow-up**:
- Update runtimes that still import legacy names (captured in subsequent phases)

### Phase 2: Planning Agent Runtime Enhancements (Optional)
**Status**: Core simplification completed – remaining items are stretch goals.
1. (Optional) Add streaming events for long-running breakdowns
2. (Optional) Capture incremental status updates for orchestrator dashboards
3. (Optional) Surface context metadata (repo, component) in streamed chunks

### Phase 3: Standardize JIRA Agent Runtime
**Target**: JIRA Agent
**Tasks**:
1. Import existing `response_formatter` module
2. Replace synchronous `agent()` with `agent.stream_async()`
3. Update entrypoint to yield streaming events
4. Replace manual response construction with formatter helpers
5. Update error handling to use `create_error_response()`
6. Reuse a common payload parser across agents (shared helper or utility)
7. Test streaming functionality end to end

### Phase 4: Standardize GitHub Agent Runtime
**Target**: GitHub Agent
**Tasks**:
1. Import existing `response_formatter` module
2. Replace synchronous `agent()` with `agent.stream_async()`
3. Update entrypoint to yield streaming events
4. Replace manual response construction with formatter
5. Update error handling to use `create_error_response()`
6. Surface OAuth token acquisition progress via streaming messages
7. Test streaming functionality

### Phase 5: Rewrite Coding Agent Runtime
**Target**: Coding Agent
**Tasks**:
1. Add AgentCore runtime entrypoint with async streaming
2. Import `common.response_formatter` for success/error payloads
3. Stream progress events for repo clone + `yarn/npm/audit` commands
4. Integrate existing workspace/test utilities in streaming loop
5. Convert command_result dicts into formatter-friendly payloads
6. Harden error handling for subprocess failures and path resolution
7. Test AgentCore deployment using a sample Node workspace

### Phase 6: Validation and Testing
**Target**: All Agents
**Tasks**:
1. Test each agent with AgentCore invoke
2. Verify streaming responses work
3. Validate response formatter usage
4. Check error handling consistency
5. Ensure OAuth flows work with streaming
6. Performance testing
7. Documentation updates

## Technical Requirements

### Response Formatter Standards
Each `response_formatter.py` currently includes:
- `AgentResponse` dataclass with standard fields
- Agent-specific formatting helpers
- Optional `clean_json_response()` or `create_error_response()` functions

Next steps:
- Confirm runtimes import and emit formatter payloads for every tool
- Add streaming-friendly helper (e.g., `format_stream_event`) where needed

### Streaming Implementation
Each runtime must:
- Use `async def` entrypoint
- Call `agent.stream_async(user_input)`
- Yield events with `async for event in stream:`
- Handle streaming errors with try/catch
- Format streamed responses consistently

### Error Handling Pattern
All agents must:
- Catch exceptions in entrypoint
- Use response formatter for error responses
- Log errors with context
- Return streaming-compatible error events
- Maintain user-friendly error messages

### AgentCore Integration
All runtimes must:
- Use `@app.entrypoint` decorator
- Accept payload parameter
- Extract user input consistently
- Return/yield proper response format
- Support both local and deployed execution

## Success Criteria

### Functional Requirements
- ✅ All agents support streaming responses
- ✅ All agents use response formatters consistently
- ✅ All agents handle errors the same way
- ✅ All agents work with AgentCore deployment
- ✅ OAuth flows work with streaming (GitHub)

### Code Quality Requirements
- ✅ No code duplication across runtimes
- ✅ Consistent import patterns
- ✅ Proper error logging
- ✅ Clean, readable code structure
- ✅ Comprehensive error handling

### Testing Requirements
- ✅ All agents deployable with AgentCore
- ✅ Streaming responses work in practice
- ✅ Error scenarios handled gracefully
- ✅ Response formats are consistent
- ✅ Performance is acceptable

## Risk Mitigation

### Breaking Changes
- Test each agent after modifications
- Keep backup of working versions
- Validate AgentCore compatibility
- Check OAuth flow integrity

### Performance Impact
- Monitor streaming response times
- Validate memory usage with streaming
- Test concurrent request handling
- Benchmark against current performance

### Integration Issues
- Test with existing tools and dependencies
- Validate model configurations
- Check environment variable handling
- Ensure backward compatibility where needed

## Timeline Estimate

- **Phase 1**: 1-2 hours (Create Planning response formatter)
- **Phase 2**: 1-2 hours (Update Planning runtime)
- **Phase 3**: 2-3 hours (Standardize JIRA runtime)
- **Phase 4**: 2-3 hours (Standardize GitHub runtime)
- **Phase 5**: 3-4 hours (Rewrite Coding runtime)
- **Phase 6**: 2-3 hours (Validation and testing)

**Total Estimated Time**: 11-17 hours

## Dependencies

### External Dependencies
- AgentCore CLI for testing
- AWS credentials for deployment testing
- OAuth configurations for GitHub agent
- JIRA instance for JIRA agent testing

### Internal Dependencies
- Existing response formatter modules
- Agent tool implementations
- Model configurations
- Environment variable setups

## Post-Implementation

### Documentation Updates
- Update agent-specific README files
- Document new streaming capabilities
- Update deployment guides
- Create troubleshooting guides

### Monitoring
- Set up logging for streaming performance
- Monitor error rates across agents
- Track response formatting consistency
- Monitor AgentCore deployment health

### Future Enhancements
- Consider response caching strategies
- Implement response compression
- Add response validation
- Consider response analytics
