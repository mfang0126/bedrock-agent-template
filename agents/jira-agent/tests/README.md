# JIRA Agent Test Suite

Comprehensive test suite for the JIRA Agent following project standards.

## Test Structure

```
tests/
├── __init__.py                  # Test package initialization
├── conftest.py                  # Shared pytest fixtures
├── test_auth_mock.py           # Mock authentication tests (10 tests)
├── test_auth_agentcore.py      # AgentCore OAuth tests (15 tests)
├── test_tools_tickets.py       # Ticket operations tests (18 tests)
├── test_tools_updates.py       # Update operations tests (21 tests)
├── test_agent.py               # Agent creation tests (15 tests)
└── integration/
    ├── __init__.py
    └── test_oauth_flow.py      # OAuth integration tests (10 tests)
```

**Total: 89 tests**

## Test Categories

### Unit Tests (79 tests)

#### Authentication Tests (25 tests)
- **test_auth_mock.py**: Mock authentication implementation
  - Token generation and consistency
  - Header formatting
  - JIRA URL configuration
  - Authentication status
  - Cloud ID handling
  - Multiple instance behavior

- **test_auth_agentcore.py**: Production OAuth implementation
  - Initialization with/without callbacks
  - OAuth URL callback triggering
  - Async callback handling
  - Token storage and retrieval
  - Cloud ID retrieval from Atlassian API
  - Error handling and fallbacks
  - Authentication headers
  - JIRA URL construction (cloud vs direct)

#### Tool Tests (39 tests)
- **test_tools_tickets.py**: Ticket operations
  - Valid/invalid ticket ID formats
  - Ticket fetching (success, not found, errors)
  - HTTP error handling (401, 404, 500, timeout)
  - Data structure validation
  - Acceptance criteria extraction
  - Unassigned tickets
  - Requirements parsing

- **test_tools_updates.py**: Update operations
  - Status updates (success, invalid transitions)
  - Case-insensitive status matching
  - Comment addition (with/without GitHub links)
  - GitHub issue/PR linking
  - Atlassian Document Format (ADF) compliance
  - API error handling
  - Validation (ticket IDs, empty values)

#### Agent Tests (15 tests)
- **test_agent.py**: Agent creation and configuration
  - Agent initialization with mock auth
  - Tool registration (5 tools)
  - System prompt configuration
  - Bedrock model configuration
  - Multiple agent instances
  - Tool injection and naming
  - Different auth implementations
  - Idempotent creation

### Integration Tests (10 tests)

#### OAuth Flow Tests
- **integration/test_oauth_flow.py**: End-to-end OAuth testing
  - OAuth URL callback flow
  - Cloud ID retrieval from Atlassian
  - Multiple site handling
  - Token storage and persistence
  - OAuth URL format validation
  - Accessible resources error handling
  - Async callback support
  - Full authentication flow simulation

## Running Tests

### Install Test Dependencies

```bash
# Using uv (preferred)
cd agents/jira-agent
uv pip install -e ".[test]"

# Using pip
pip install -e ".[test]"
```

### Run All Tests

```bash
# Run all unit tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src --cov-report=term-missing --cov-report=html
```

### Run Specific Test Categories

```bash
# Run only unit tests (exclude integration)
pytest -m "not integration"

# Run only authentication tests
pytest tests/test_auth_*.py

# Run only tool tests
pytest tests/test_tools_*.py

# Run only agent tests
pytest tests/test_agent.py

# Run only integration tests (requires deployed resources)
INTEGRATION_TESTS=true pytest -m integration

# Run only fast tests (exclude slow)
pytest -m "not slow"
```

### Run Specific Test Files

```bash
# Mock authentication tests
pytest tests/test_auth_mock.py

# AgentCore authentication tests
pytest tests/test_auth_agentcore.py

# Ticket tool tests
pytest tests/test_tools_tickets.py

# Update tool tests
pytest tests/test_tools_updates.py

# Agent creation tests
pytest tests/test_agent.py

# OAuth integration tests
pytest tests/integration/test_oauth_flow.py
```

### Run Specific Tests

```bash
# Run specific test by name
pytest tests/test_auth_mock.py::TestMockJiraAuth::test_mock_auth_returns_token

# Run all tests in a class
pytest tests/test_tools_tickets.py::TestFetchJiraTicket

# Run tests matching pattern
pytest -k "ticket" -v
pytest -k "oauth" -v
pytest -k "error_handling" -v
```

## Test Markers

Tests are organized with pytest markers:

- `@pytest.mark.integration` - Integration tests requiring deployed resources
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.asyncio` - Async tests (auto-detected by pytest-asyncio)

### Using Markers

```bash
# Run only integration tests
pytest -m integration

# Exclude integration tests
pytest -m "not integration"

# Exclude slow tests
pytest -m "not slow"

# Run integration and slow tests
pytest -m "integration or slow"
```

## Coverage Goals

### Target Coverage Percentages

- **Authentication implementations**: >90%
  - MockJiraAuth: 100%
  - AgentCoreJiraAuth: >85%

- **Tool methods**: >85%
  - JiraTicketTools: >90%
  - JiraUpdateTools: >90%

- **Agent creation**: 100%
  - create_jira_agent: 100%

### Generate Coverage Report

```bash
# Terminal report
pytest --cov=src --cov-report=term-missing

# HTML report (opens in browser)
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Both terminal and HTML
pytest --cov=src --cov-report=term-missing --cov-report=html

# Fail if coverage below 85%
pytest --cov=src --cov-fail-under=85
```

## Key Test Scenarios Covered

### Authentication
✅ Mock auth token generation and consistency
✅ OAuth URL callback triggering
✅ Cloud ID retrieval from Atlassian API
✅ Token storage and authentication state
✅ Error handling for API failures
✅ Multiple site handling
✅ Async callback support

### Ticket Operations
✅ Valid ticket ID formats (PROJ-123, ABC-456)
✅ Invalid formats (lowercase, missing parts, too long/short)
✅ Ticket fetching (200, 404, 401, 500 responses)
✅ Timeout handling
✅ Data structure validation
✅ Acceptance criteria extraction
✅ Requirements parsing for Planning Agent

### Update Operations
✅ Status transitions (valid and invalid)
✅ Case-insensitive status matching
✅ Available transitions in error messages
✅ Comment addition with ADF format
✅ GitHub URL inclusion in comments
✅ Remote link creation (issues and PRs)
✅ Validation (ticket IDs, empty values, URLs)

### Agent Creation
✅ Initialization with different auth implementations
✅ Tool registration (all 5 tools present)
✅ System prompt configuration
✅ Bedrock model configuration
✅ Environment variable handling
✅ Multiple instance creation
✅ Protocol-based interface compliance

## Fixtures

### Authentication Fixtures
- `mock_auth`: MockJiraAuth instance
- `ticket_tools`: JiraTicketTools with mock auth
- `update_tools`: JiraUpdateTools with mock auth
- `mock_httpx_client`: Async HTTP client for testing

### Mock Response Fixtures
- `mock_ticket_response`: JIRA ticket API response
- `mock_transitions_response`: Status transitions response
- `mock_comment_response`: Comment creation response
- `mock_remotelink_response`: Remote link response

### Environment Fixtures
- `setup_test_env`: Auto-used fixture for clean environment

## Testing Best Practices

### 1. Use Fixtures for Common Setup
```python
def test_example(mock_auth, ticket_tools):
    # Auth and tools already configured
    result = await ticket_tools.fetch_jira_ticket("PROJ-123")
```

### 2. Mock External API Calls
```python
@pytest.mark.asyncio
async def test_api_call(ticket_tools, httpx_mock):
    httpx_mock.add_response(
        url="https://test.atlassian.net/rest/api/3/issue/PROJ-123",
        json={"key": "PROJ-123"},
        status_code=200
    )
    result = await ticket_tools.fetch_jira_ticket("PROJ-123")
```

### 3. Test Both Success and Error Cases
```python
async def test_success_case(ticket_tools, httpx_mock):
    # Mock successful response
    httpx_mock.add_response(status_code=200, json={...})

async def test_error_case(ticket_tools, httpx_mock):
    # Mock error response
    httpx_mock.add_response(status_code=404)
```

### 4. Verify Response Structure
```python
result = await tool.some_method(...)
assert result["success"] is True
assert "data" in result
assert "message" in result
assert result["data"]["field"] == expected_value
```

## Integration Tests

Integration tests require deployed AgentCore resources and are skipped by default.

### Prerequisites
1. Deployed JIRA agent runtime
2. Configured Jira provider in AgentCore Identity
3. Valid OAuth credentials
4. INTEGRATION_TESTS environment variable set to "true"

### Running Integration Tests
```bash
# Enable integration tests
export INTEGRATION_TESTS=true

# Run integration tests
pytest -m integration

# Run specific integration test
pytest tests/integration/test_oauth_flow.py::TestOAuthFlow::test_cloud_id_retrieval
```

### Integration Test Notes
- Tests are skipped if `INTEGRATION_TESTS != "true"`
- Requires real OAuth flow completion
- May require browser interaction
- Tests use real Atlassian API endpoints
- Tests verify end-to-end authentication flow

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e ".[test]"
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Import Errors
```bash
# Ensure package is installed in editable mode
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

### Async Test Errors
```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Check asyncio_mode in pytest.ini
# Should be set to "auto"
```

### HTTPX Mock Not Working
```bash
# Ensure pytest-httpx is installed
pip install pytest-httpx

# Use httpx_mock fixture correctly
def test_example(httpx_mock):
    httpx_mock.add_response(...)
```

### Coverage Issues
```bash
# Generate detailed coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Check which lines are not covered
pytest --cov=src --cov-report=term-missing
```

## Maintenance

### Adding New Tests
1. Create test file in appropriate directory
2. Import required fixtures from conftest.py
3. Follow naming convention: `test_<module>_<scenario>`
4. Use descriptive test names and docstrings
5. Test both success and error cases
6. Verify structured response format

### Updating Fixtures
1. Edit `conftest.py` to modify shared fixtures
2. Ensure changes don't break existing tests
3. Run full test suite to verify
4. Update documentation if needed

### Test Naming Conventions
- File: `test_<module>.py`
- Class: `Test<ClassName>`
- Function: `test_<function>_<scenario>`
- Mark integration tests with `@pytest.mark.integration`
- Mark slow tests with `@pytest.mark.slow`

## Test Quality Checklist

- [x] All tests have descriptive names
- [x] All tests have docstrings explaining purpose
- [x] Both success and error cases tested
- [x] Response structure validation
- [x] Mock external API calls (no real network)
- [x] Async tests use `@pytest.mark.asyncio`
- [x] Integration tests properly marked
- [x] Coverage >85% for critical paths
- [x] Tests are independent and isolated
- [x] Fixtures used for common setup

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-httpx](https://colin-b.github.io/pytest_httpx/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [JIRA REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Atlassian OAuth 2.0](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/)
