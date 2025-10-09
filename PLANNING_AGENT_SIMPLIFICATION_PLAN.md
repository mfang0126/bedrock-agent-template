# Planning Agent Simplification Notes

## Current Snapshot (Completed)
- **Tools**: reduced to a single lightweight helper `tools/task_planner.py` that returns
  deterministic task breakdowns for prompts like “help me audit the repo vulnerability”.
- **Agent entrypoints**: `agent.py` simply wraps the `breakdown_task` helper and exposes
  JSON formatting utilities (no Strands/Bedrock dependency).
- **Runtime**: `runtime.py` provides a minimal AgentCore entrypoint that calls the tool and
  wraps results with the shared response formatter (no streaming, no Bedrock dependency).
- **CLI**: `src/__main__.py` offers a dependency-free argparse command for local testing.
- **Legacy modules removed**: the former `tools/planning`, `tools/coding`, and
  `tools/orchestrator` trees were deleted along with async helpers and validation utilities
  that depended on Bedrock or multi-agent orchestration.

## Output Format
`breakdown_task` returns a dictionary with:
- `title`, `summary`
- Ordered `phases` (each with `title`, `tasks`, `duration`)
- Derived `dependencies`, `risk_level`, and `estimated_effort`
The runtime feeds this into `format_planning_response`, so orchestrator callers receive
consistent `AgentResponse` envelopes.

## Remaining Opportunities
1. **Streaming (optional)** – add incremental updates if the orchestrator expects streaming
   events. Current runtime returns a single payload which already works for synchronous
   invocations.
2. **Context enrichment** – extend `breakdown_task` to use optional repo metadata (language,
   framework) if provided by the orchestrator payload.
3. **Plan templates** – add more keyword templates beyond security audits and generic feature
   work as new workflows emerge.
4. **Tests** – add a small unit test harness for `task_planner` to keep regression coverage
   once the repo adds automated testing.

## Hand-off Checklist
- Orchestrator can invoke the runtime by sending `{"prompt": "<task>"}` and consuming the
  returned `AgentResponse` data.
- Coding agent retains responsibility for cloning repos and running yarn/npm audits as part
  of follow-up execution tasks.
