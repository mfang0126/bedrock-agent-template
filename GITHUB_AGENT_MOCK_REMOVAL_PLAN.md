# GitHub Agent Mock Code Removal Plan

## Overview
This document outlines the comprehensive plan to remove all mock code from the GitHub Agent and ensure all tools use real GitHub API implementations. The agent currently has extensive mock functionality that bypasses real API calls for development/testing purposes.

## Current Mock Code Analysis

### Mock Code Locations
1. **`src/__main__.py`** - CLI mock mode checks and mock authentication flows
2. **`src/agent.py`** - Mock response generation in `run_agent_query()` function  
3. **`src/common/config/config.py`** - Missing `is_mock_mode()` method (referenced but not implemented)

### Real Implementation Status
- ✅ **GitHub Tools**: `tools/github/repos.py`, `tools/github/issues.py`, `tools/github/pull_requests.py` are real implementations
- ✅ **Authentication**: `common/auth/github.py` has real OAuth implementation structure
- ✅ **Configuration**: `common/config/config.py` has real credential management

## Implementation Plan

### Phase 1: Fix Missing Configuration Method
**Objective**: Implement the missing `is_mock_mode()` method to prevent runtime errors

**Tasks**:
1. Add `is_mock_mode()` method to `Config` class in `src/common/config/config.py`
2. Method should check `MOCK_MODE` environment variable (default: False for production)
3. Ensure backward compatibility during transition

**Files Modified**:
- `src/common/config/config.py`

**Implementation**:
```python
def is_mock_mode(self) -> bool:
    """Check if running in mock mode.
    
    Returns:
        True if MOCK_MODE=true in environment, False otherwise
    """
    return os.getenv("MOCK_MODE", "false").lower() == "true"
```

### Phase 2: Remove Mock Logic from Agent Core
**Objective**: Eliminate mock response generation and ensure agent always uses real tools

**Tasks**:
1. Remove mock mode parameter from `create_github_agent()` function
2. Remove mock response logic from `run_agent_query()` function
3. Ensure agent always initializes with real Bedrock model and tools
4. Remove mock data generation (hardcoded repos, issues, etc.)

**Files Modified**:
- `src/agent.py`

**Key Changes**:
- Remove `mock_mode` parameter from function signatures
- Remove entire mock response generation block (lines 83-126)
- Ensure agent always calls real tools through Strands framework
- Improve error handling for Bedrock model initialization

### Phase 3: Simplify CLI Interface
**Objective**: Remove mock mode checks and ensure CLI always uses real agent

**Tasks**:
1. Remove `config.is_mock_mode()` checks from all CLI commands
2. Remove mock authentication simulation in `auth()` command
3. Implement real OAuth device flow in `auth()` command
4. Remove mock mode warnings and messages
5. Update help text and command descriptions

**Files Modified**:
- `src/__main__.py`

**Key Changes**:
- Remove mock mode conditional logic from `invoke()` command
- Implement real OAuth device flow in `auth()` command
- Remove mock mode status from `show_config()` command
- Update CLI help text to reflect real functionality

### Phase 4: Enhance Real Tool Implementation
**Objective**: Ensure all GitHub tools are robust and production-ready

**Tasks**:
1. Review and enhance error handling in GitHub tools
2. Add proper authentication token validation
3. Implement comprehensive logging for debugging
4. Add rate limiting and retry logic for API calls
5. Ensure all tools handle edge cases properly

**Files Modified**:
- `src/tools/github/repos.py`
- `src/tools/github/issues.py`
- `src/tools/github/pull_requests.py`

### Phase 5: Update Configuration and Environment
**Objective**: Ensure production-ready configuration management

**Tasks**:
1. Remove `MOCK_MODE` environment variable references
2. Update `.env.example` to remove mock mode configuration
3. Ensure all required environment variables are documented
4. Add validation for required GitHub OAuth credentials

**Files Modified**:
- `src/common/config/config.py`
- `.env.example` (if exists)
- Documentation files

### Phase 6: Clean Up and Testing
**Objective**: Remove all mock-related code and ensure functionality

**Tasks**:
1. Remove any remaining mock-related imports or references
2. Clean up unused mock data structures
3. Update docstrings and comments to reflect real functionality
4. Test all CLI commands with real GitHub API
5. Verify OAuth authentication flow works correctly

## Success Criteria

### Functional Requirements
- [ ] All CLI commands work with real GitHub API
- [ ] OAuth device flow authentication works correctly
- [ ] All GitHub tools (repos, issues, pull requests) function properly
- [ ] Error handling provides meaningful feedback
- [ ] No mock mode references remain in codebase

### Technical Requirements
- [ ] No `mock_mode` parameters in function signatures
- [ ] No hardcoded mock data in responses
- [ ] All tools use real httpx HTTP client for API calls
- [ ] Proper error handling for network and authentication failures
- [ ] Clean, production-ready code without development artifacts

### User Experience
- [ ] Clear error messages when authentication is required
- [ ] Helpful guidance for setting up GitHub OAuth credentials
- [ ] Consistent behavior across all commands
- [ ] No confusing mock mode warnings or messages

## Risk Mitigation

### Authentication Issues
- **Risk**: Users may not have GitHub OAuth credentials configured
- **Mitigation**: Provide clear error messages and setup instructions
- **Fallback**: Comprehensive documentation for OAuth app creation

### API Rate Limiting
- **Risk**: GitHub API rate limits may cause failures
- **Mitigation**: Implement proper retry logic and rate limit handling
- **Monitoring**: Add logging to track API usage patterns

### Backward Compatibility
- **Risk**: Existing users may rely on mock mode for testing
- **Mitigation**: Document migration path and provide testing alternatives
- **Communication**: Clear changelog and migration guide

## Timeline Estimate

- **Phase 1**: 1-2 hours (Fix configuration method)
- **Phase 2**: 2-3 hours (Remove agent mock logic)
- **Phase 3**: 2-3 hours (Simplify CLI interface)
- **Phase 4**: 3-4 hours (Enhance real tools)
- **Phase 5**: 1-2 hours (Update configuration)
- **Phase 6**: 2-3 hours (Clean up and testing)

**Total Estimated Time**: 11-17 hours

## Dependencies

### Required Environment Variables
```bash
GITHUB_CLIENT_ID=your_github_oauth_app_client_id
GITHUB_CLIENT_SECRET=your_github_oauth_app_client_secret
AWS_REGION=ap-southeast-2  # For Bedrock model
```

### Required AWS Permissions
- Bedrock model access for Claude 3.5 Sonnet
- Appropriate IAM permissions for model invocation

### GitHub OAuth App Requirements
- OAuth App created at https://github.com/settings/developers
- Device Flow authorization enabled
- Appropriate callback URLs configured

## Post-Implementation Validation

### Manual Testing Checklist
- [ ] `github-agent invoke "list my repositories"` returns real repos
- [ ] `github-agent invoke "create a repository called test-repo"` creates real repo
- [ ] `github-agent invoke "list issues in owner/repo"` returns real issues
- [ ] `github-agent auth` completes OAuth device flow successfully
- [ ] Error handling works for invalid credentials
- [ ] Error handling works for network failures

### Automated Testing
- [ ] Unit tests for all GitHub tools
- [ ] Integration tests with GitHub API (using test credentials)
- [ ] CLI command tests
- [ ] Authentication flow tests

## Benefits of Mock Removal

### Production Readiness
- Agent becomes fully functional for real GitHub operations
- No confusion between mock and real behavior
- Proper error handling for production scenarios

### Code Quality
- Cleaner, more maintainable codebase
- Reduced complexity and conditional logic
- Better separation of concerns

### User Experience
- Consistent, predictable behavior
- Real GitHub integration from day one
- Clear setup and configuration process

### Development Efficiency
- Faster development cycles without mock maintenance
- Real API testing during development
- Better debugging with actual API responses

---

**Note**: This plan assumes the existing real GitHub tools are functional and properly implemented. Any issues discovered during implementation should be addressed as part of Phase 4 (Enhance Real Tool Implementation).