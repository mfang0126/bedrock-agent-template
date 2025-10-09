# Clean JSON Functions for Agent Responses

This document explains the lightweight response-formatting helpers that ship with each agent. Every agent keeps its formatter module close to the runtime so that response types stay simple and easy to extend.

## Overview

Each agent exposes a dedicated formatter module:
- Planning: `agents/planning-agent/src/common/response_formatter.py`
- GitHub: `agents/github-agent/src/common/response_formatter.py`
- JIRA: `agents/jira-agent/src/common/response_formatter.py`

Every formatter provides two core helpers:
1. `clean_json_response` – normalizes free-form strings into a structured response object.
2. `format_*_response` – builds a typed response for the agent's most common actions.

All helpers return dataclasses with `success`, `message`, `data`, `timestamp`, and `agent_type` fields.

## Planning Agent Helpers

### `clean_json_response(raw_response: str, agent_type: str = "planning") -> AgentResponse`

Parses loosely formatted responses from the planning tools and wraps them in a consistent structure.

```python
from common.response_formatter import clean_json_response

raw = """Some logs...\n{\"message\": \"ok\", \"data\": {\"plan\": []}}"""
normalized = clean_json_response(raw)
print(normalized.to_json())
```

### `format_planning_response(plan_data: Dict[str, Any], requirements: str | None = None, validation_results: Dict[str, Any] | None = None, success: bool = True) -> AgentResponse`

Builds a response for plan-generation flows. The helper synthesizes a summary message using the number of phases and optional timeline metadata.

```python
from common.response_formatter import format_planning_response

plan = {
    "phases": [{"title": "Preparation", "tasks": ["Review request"], "duration": "0.5 day"}],
    "estimated_effort": "2-3 days",
}
response = format_planning_response(plan, requirements="Add SSO support")
print(response.message)
```

## GitHub Agent Helpers

### `clean_json_response(raw_response: str, agent_type: str = "github") -> AgentResponse`

Cleans raw GitHub agent output, defaulting the agent type to `github`.

### `format_github_response(action: str, result_data: Dict[str, Any], repository: str | None = None, success: bool = True) -> AgentResponse`

Creates a contextual GitHub result message and wraps it in `AgentResponse`.

```python
from common.response_formatter import format_github_response

repos = [{"name": "repo1", "stars": 10}]
formatted = format_github_response("list_repos", repos)
```

## JIRA Agent Helpers

### `clean_json_response(raw_response: str, agent_type: str = "jira") -> AgentResponse`

Normalizes responses coming back from the JIRA workflow helpers.

### `format_jira_response(action: str, result_data: Dict[str, Any], ticket_id: str | None = None, success: bool = True) -> AgentResponse`

Produces a structured payload summarizing JIRA operations such as fetching tickets or adding comments.

```python
from common.response_formatter import format_jira_response

summary = {"key": "PROJ-1", "summary": "Fix login"}
formatted = format_jira_response("fetch_ticket", summary)
```

## Integration Notes

### Planning Agent (`agents/planning-agent/src/agent.py`)

```python
from common.response_formatter import clean_json_response, format_planning_response
```

### GitHub Agent (`agents/github-agent/src/agent.py`)

```python
from common.response_formatter import clean_json_response, format_github_response
```

### JIRA Agent (helpers in `agents/jira-agent/src/runtime.py`)

```python
from common.response_formatter import clean_json_response, format_jira_response
```

## Example Demo

Run `python examples/simple_clean_demo.py` to see the planning and GitHub helpers exercised with sample payloads. Add similar snippets for the JIRA formatter when end-to-end tooling is available.

## Benefits

- **Consistency** – Every agent returns the same envelope structure.
- **Simplicity** – Each module exports only the helpers it actively uses.
- **Traceability** – Responses include UTC timestamps and agent identifiers.
- **Extensibility** – Adding a new agent only requires a focused formatter module.
