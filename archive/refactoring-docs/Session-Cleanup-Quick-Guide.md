# Session Cleanup Quick Guide

## Overview

Automatic workspace cleanup after each coding session to keep workspaces organized and prevent clutter.

## How It Works

### Automatic Session Archiving

At the end of each session, the Coding Agent automatically:

1. **Identifies Session Work**
   - Files created during the session
   - Modified files
   - Generated outputs and logs

2. **Archives Everything**
   ```
   workspace/
   └── .archive/
       └── session_20251010_143022/
           ├── session_summary.json
           ├── src/
           │   └── app.js
           └── package.json
   ```

3. **Cleans Temporary Files**
   - `*.tmp`, `*.temp`, `*.log`
   - `__pycache__`, `*.pyc`, `.pytest_cache`
   - `node_modules/.cache`, `.DS_Store`

4. **Verifies Clean State**
   - Workspace is clean and ready for next session
   - No temporary files left behind

## New Tools

### `archive_session_work()`
```python
# Archive current session work
result = archive_session_work(
    session_id="custom_session_name",  # Optional: auto-generated if not provided
    cleanup_temp=True                  # Clean temporary files
)

# Returns:
{
    "success": True,
    "session_id": "session_20251010_143022",
    "total_archived": 15,
    "temp_files_removed": 8,
    "archive_location": "/tmp/coding_workspace/.archive/session_20251010_143022",
    "workspace_clean": True,
    "message": "Session archived. Workspace cleaned."
}
```

### `list_archived_sessions()`
```python
# List all archived sessions
sessions = list_archived_sessions()

# Returns:
{
    "success": True,
    "sessions": [
        {
            "session_id": "session_20251010_143022",
            "archived_at": "2025-10-10T14:30:22",
            "files_archived": 15,
            "archive_location": "/tmp/coding_workspace/.archive/session_20251010_143022"
        },
        # ... more sessions
    ],
    "total_sessions": 5
}
```

### `restore_session()`
```python
# Restore files from a previous session
result = restore_session("session_20251010_143022")

# Returns:
{
    "success": True,
    "session_id": "session_20251010_143022",
    "files_restored": ["src/app.js", "package.json", "..."],
    "total_restored": 15,
    "message": "Restored 15 files from session_20251010_143022"
}
```

## Usage Examples

### Example 1: Normal Workflow
```
1. Developer: "Create a Node.js app with Express"
2. Coding Agent: Creates project, installs dependencies
3. Developer: "I'm done for now"
4. Coding Agent: Automatically calls archive_session_work()
   → Archives all files to .archive/session_20251010_143022/
   → Cleans temporary files
   → Workspace is clean for next session
```

### Example 2: Manual Archive
```
Developer: "Archive this session before I move to something else"
Coding Agent: archive_session_work(session_id="express_app_setup")
→ Archives with custom name: .archive/express_app_setup/
```

### Example 3: Restore Previous Work
```
Developer: "Restore my work from yesterday"
Coding Agent:
  1. list_archived_sessions() → Shows all sessions
  2. Developer selects: "session_20251009_153045"
  3. restore_session("session_20251009_153045")
  → All files restored to workspace
```

## Archive Structure

```
/tmp/coding_workspace/
├── .archive/                      # Archive root (never deleted)
│   ├── session_20251010_100000/  # Each session has its own folder
│   │   ├── session_summary.json  # Metadata about the session
│   │   ├── src/                  # Original directory structure preserved
│   │   │   └── app.js
│   │   └── package.json
│   ├── session_20251010_140000/
│   │   ├── session_summary.json
│   │   └── test/
│   │       └── test.js
│   └── express_app_setup/        # Custom named session
│       ├── session_summary.json
│       └── ...
└── [empty workspace ready for next session]
```

## Session Summary Format

Each archived session includes a `session_summary.json`:

```json
{
  "session_id": "session_20251010_143022",
  "archived_at": "2025-10-10T14:30:22.123456",
  "files_archived": 15,
  "temp_files_removed": 8,
  "archive_location": "/tmp/coding_workspace/.archive/session_20251010_143022",
  "workspace_state": "clean"
}
```

## Benefits

### For Developers
- ✅ **Clean Workspace**: Start each session with a clean slate
- ✅ **Session History**: All previous work is preserved and accessible
- ✅ **Easy Recovery**: Restore any previous session if needed
- ✅ **No Clutter**: Temporary files automatically cleaned up

### For Stability
- ✅ **Predictable State**: Workspace always in known clean state
- ✅ **Isolation**: Each session's work is isolated
- ✅ **Debugging**: Can inspect previous sessions to understand issues
- ✅ **Rollback**: Can restore to any previous session state

## Configuration

### Environment Variables
```bash
# Default workspace root
WORKSPACE_ROOT="/tmp/coding_workspace"

# Archive is always at: $WORKSPACE_ROOT/.archive/
```

### Automatic Cleanup Patterns
Default patterns cleaned automatically:
- `*.tmp`, `*.temp`, `*.log`
- `__pycache__/`, `*.pyc`, `.pytest_cache/`
- `node_modules/.cache/`, `.DS_Store`
- Any directory named `.cache` or `__pycache__`

### Exclusions
Files/directories NEVER archived or deleted:
- `.archive/` - The archive directory itself
- `.git/` - Git repository (if present)
- `node_modules/` - Keep node_modules in place (only cache cleaned)

## Best Practices

### 1. Let It Archive Automatically
The Coding Agent will automatically archive at session end. No manual intervention needed.

### 2. Use Custom Names for Important Sessions
```python
archive_session_work(session_id="important_feature_v1")
```

### 3. Review Archives Periodically
```python
list_archived_sessions()  # See what's been archived
```

### 4. Clean Up Old Archives (Manual)
Archives don't auto-delete. Manually clean old ones if needed:
```bash
rm -rf /tmp/coding_workspace/.archive/session_20251001_*
```

## Troubleshooting

### Q: What if I need a file after it's archived?
A: Use `restore_session(session_id)` to restore all files from that session.

### Q: Can I prevent specific files from being archived?
A: Currently all non-archive files are archived. In future, we can add `.archiveignore` support.

### Q: What happens if archive fails?
A: Session continues normally. Archive is best-effort and won't block work.

### Q: How much disk space do archives use?
A: Depends on your work. Monitor with `du -sh /tmp/coding_workspace/.archive/`

## Implementation Status

- [x] Workflow designed
- [x] Tools implemented in design document
- [x] **COMPLETED**: Add to Coding Agent's agent.py
- [x] **COMPLETED**: Add to Coding Agent's system prompt
- [x] **COMPLETED**: Deploy to AWS (codingagent-lE7IQU3dK8)
- [ ] **TODO**: Test with real sessions
- [ ] **TODO**: Monitor and refine based on usage

## Next Steps

1. ✅ ~~Implement the 3 tools in `agents/coding-agent/src/agent.py`~~ - **COMPLETED**
2. ✅ ~~Update Coding Agent system prompt to call `archive_session_work()` at session end~~ - **COMPLETED**
3. ✅ ~~Deploy updated Coding Agent~~ - **DEPLOYED** (arn:aws:bedrock-agentcore:ap-southeast-2:670326884047:runtime/codingagent-lE7IQU3dK8)
4. Test with real coding sessions
5. Monitor and refine based on usage feedback
