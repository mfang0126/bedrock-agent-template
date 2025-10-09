# Coding Agent Workspace Setup Workflow

The Coding Agent now focuses on a streamlined Node.js workflow:

1. Clone or update a repository into an isolated workspace.
2. Run `yarn install`, `npm install`, and `npm audit --json` (or any custom command list).
3. Return structured command results to the caller.

## Tool entrypoint

The Strands agent exposes the `setup_workspace` tool defined in `agents/coding-agent/src/coding_agent.py`. Example usage from another agent or a test harness:

```python
from agents.coding_agent.src.coding_agent import setup_workspace

result = setup_workspace(
    workspace_path="node-workspaces/sample",
    dependencies={
        "repo_url": "https://github.com/example/project.git",
        "branch": "main",
        "commands": [
            "yarn install",
            "npm install",
            "npm audit --json"
        ]
    }
)
print(result["command_results"][0]["stdout"])
```

## Return payload

`setup_workspace` responds with the following keys:

- `success`: Overall status (false when any command fails)
- `workspace_path`: Absolute path to the prepared workspace
- `repo_url` / `branch`: Optional git metadata if provided
- `commands_executed`: The list of commands executed
- `command_results`: A list of per-command dictionaries capturing stdout/stderr/exit codes

## Defaults

If no repo URL is provided, the function simply runs the command list in the existing workspace directory. When no command list is provided, it defaults to:

```text
yarn install
npm install
npm audit --json
```

## Notes

- The workspace manager resolves relative paths against the `WORKSPACE_ROOT` environment variable (defaults to `/tmp/coding_workspace`).
- Git clone is skipped when the workspace already contains a `.git` directory; instead, a `git pull origin <branch>` is issued.
- Command output is captured verbatim for downstream summarization.
