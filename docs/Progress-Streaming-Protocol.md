# Progress Streaming Protocol

## Overview

Real-time progress updates ensure developers know exactly what's happening during agent operations. This is critical for:
- **Transparency**: Know what the agent is doing
- **Debugging**: See where things go wrong
- **Confidence**: Trust the agent is working correctly
- **Cancellation**: Ability to stop if things look wrong

## Streaming Pattern

All long-running operations must stream progress using `yield` statements:

```python
@app.entrypoint
async def agent_function(payload):
    """Agent with progress streaming."""

    # Step 1: Announce what you're doing
    yield "🔍 Starting dependency audit...\n"

    # Step 2: Stream progress during execution
    yield "  → Detecting package manager (npm/yarn)...\n"
    package_manager = detect_package_manager()
    yield f"  ✓ Found: {package_manager}\n\n"

    # Step 3: Show what's executing
    yield f"📦 Running `{package_manager} audit`...\n"
    result = run_audit()

    # Step 4: Stream results incrementally
    yield "  → Parsing results...\n"
    vulnerabilities = parse_results(result)
    yield f"  ✓ Found {len(vulnerabilities)} vulnerabilities\n\n"

    # Step 5: Final summary
    yield "✅ Audit complete\n"
```

## Progress Message Format

### Standard Prefixes

```python
# Status indicators
"🔍"  # Starting/Analyzing
"📦"  # Package/Dependency operations
"🔧"  # Fixing/Modifying
"✅"  # Success
"⚠️"  # Warning
"❌"  # Error/Failure
"📝"  # Creating/Writing
"🗑️"  # Deleting/Cleaning
"💾"  # Saving/Archiving
"🔄"  # In progress/Working
"→"   # Sub-step indicator
"✓"   # Sub-step complete
```

### Message Structure

```python
# Pattern: [Emoji] [Action] [Target] [Status]

yield "🔍 Analyzing dependencies in package.json...\n"
yield "  → Checking for vulnerabilities...\n"
yield "  ✓ Analysis complete\n"
yield "  → Found 3 high-severity issues\n\n"

yield "🔧 Attempting to fix vulnerabilities...\n"
yield "  → Running npm audit fix...\n"
yield "  ⚠️ Some packages cannot be auto-fixed\n\n"

yield "✅ Fixed 2 out of 3 vulnerabilities\n"
```

## Implementation Examples

### Example 1: Safe Dependency Update (with streaming)

```python
@tool
def safe_dependency_update_streaming(
    packages: List[str],
    update_type: str = "patch"
) -> Generator[str, None, Dict]:
    """Update dependencies with progress streaming."""

    # Announce start
    yield f"🔍 Starting dependency update for {len(packages)} packages...\n\n"

    # Step 1: Create checkpoint
    yield "💾 Creating safety checkpoint...\n"
    yield "  → Saving current package.json\n"
    yield "  → Saving current lock file\n"
    yield "  → Running initial tests\n"

    snapshot = create_checkpoint()
    checkpoint_id = snapshot["id"]

    yield f"  ✓ Checkpoint created: {checkpoint_id}\n\n"

    # Step 2: Analyze impact
    yield "🔍 Analyzing update impact...\n"

    for package in packages:
        yield f"  → Checking {package} for breaking changes...\n"
        impact = check_breaking_changes(package)

        if impact["has_breaking_changes"]:
            yield f"  ⚠️ {package}: Breaking changes detected\n"
        else:
            yield f"  ✓ {package}: Safe to update\n"

    yield "\n"

    # Step 3: Execute updates
    yield f"📦 Updating {len(packages)} packages...\n"

    for i, package in enumerate(packages, 1):
        yield f"  → [{i}/{len(packages)}] Updating {package}...\n"

        update_result = update_package(package, update_type)

        if update_result["success"]:
            yield f"  ✓ {package}: {update_result['old_version']} → {update_result['new_version']}\n"
        else:
            yield f"  ❌ {package}: Update failed - {update_result['error']}\n"

    yield "\n"

    # Step 4: Validation
    yield "🔍 Validating updates...\n"
    yield "  → Running test suite...\n"

    test_result = run_all_tests()

    if test_result["passed"]:
        yield f"  ✅ All {test_result['total']} tests passed\n\n"

        # Success - commit
        yield "💾 Saving changes...\n"
        commit_changes("Update dependencies")
        yield "  ✓ Changes committed\n\n"

        yield "✅ Dependency update successful!\n"

        return {
            "success": True,
            "packages_updated": packages,
            "checkpoint_id": checkpoint_id
        }

    else:
        # Failure - rollback
        yield f"  ❌ {test_result['failed']} tests failed\n\n"

        yield "🔄 Rolling back to checkpoint...\n"
        yield f"  → Restoring {checkpoint_id}...\n"

        rollback_to_checkpoint(checkpoint_id)

        yield "  ✓ Rollback complete\n\n"
        yield "❌ Update failed - rolled back to safe state\n"

        return {
            "success": False,
            "rolled_back": True,
            "checkpoint_id": checkpoint_id,
            "test_failures": test_result["failures"]
        }
```

### Example 2: Session Archiving (with streaming)

```python
@tool
def archive_session_work_streaming(
    session_id: str = None,
    cleanup_temp: bool = True
) -> Generator[str, None, Dict]:
    """Archive session with progress streaming."""

    if not session_id:
        session_id = datetime.now().strftime("session_%Y%m%d_%H%M%S")

    yield f"💾 Archiving session: {session_id}\n\n"

    # Step 1: Identify files
    yield "🔍 Identifying session files...\n"

    session_files = identify_session_files(workspace_root)

    yield f"  ✓ Found {len(session_files)} files to archive\n\n"

    # Step 2: Create archive directory
    yield "📁 Creating archive directory...\n"

    archive_path = create_archive_directory(session_id)

    yield f"  ✓ Archive: {archive_path}\n\n"

    # Step 3: Archive files
    yield f"💾 Archiving {len(session_files)} files...\n"

    archived_count = 0
    for file_path in session_files:
        # Show progress every 10 files or for important files
        if archived_count % 10 == 0 or is_important_file(file_path):
            rel_path = os.path.relpath(file_path, workspace_root)
            yield f"  → Archiving {rel_path}...\n"

        archive_file(file_path, archive_path)
        archived_count += 1

    yield f"  ✓ Archived {archived_count} files\n\n"

    # Step 4: Clean temporary files
    if cleanup_temp:
        yield "🗑️ Cleaning temporary files...\n"

        temp_files = find_temp_files(workspace_root)
        yield f"  → Found {len(temp_files)} temporary files\n"

        for temp_file in temp_files:
            remove_file(temp_file)

        yield f"  ✓ Removed {len(temp_files)} temporary files\n\n"

    # Step 5: Verify
    yield "🔍 Verifying workspace...\n"

    verification = verify_workspace_clean(workspace_root)

    if verification["clean"]:
        yield "  ✅ Workspace is clean\n\n"
    else:
        yield f"  ⚠️ {verification['issues']} issues found\n\n"

    # Final summary
    yield "✅ Session archiving complete\n"
    yield f"📁 Archive location: {archive_path}\n"

    return {
        "success": True,
        "session_id": session_id,
        "files_archived": archived_count,
        "temp_files_removed": len(temp_files) if cleanup_temp else 0,
        "archive_location": archive_path,
        "workspace_clean": verification["clean"]
    }
```

### Example 3: Orchestrator Workflow (with streaming)

```python
@app.entrypoint
async def strands_agent_orchestrator(payload: Dict[str, Any]):
    """Orchestrator with detailed progress streaming."""

    user_input = _extract_user_input(payload)

    if not user_input:
        yield "Hello! I'm the Orchestrator Agent.\n"
        return

    yield f"🎯 Task received: {user_input}\n\n"

    # Step 1: Analyze task
    yield "🔍 Analyzing task requirements...\n"

    task_analysis = analyze_task(user_input)

    yield f"  → Task type: {task_analysis['type']}\n"
    yield f"  → Agents needed: {', '.join(task_analysis['agents'])}\n"
    yield f"  → Estimated steps: {len(task_analysis['steps'])}\n\n"

    # Step 2: Validate environment
    yield "🔍 Validating environment...\n"

    validation = validate_environment()

    if not validation["safe"]:
        yield f"  ❌ Environment validation failed:\n"
        for issue in validation["issues"]:
            yield f"    - {issue}\n"
        yield "\n⛔ Cannot proceed with current environment\n"
        return

    yield "  ✅ Environment is safe\n\n"

    # Step 3: Execute workflow
    yield f"🚀 Starting workflow with {len(task_analysis['steps'])} steps...\n\n"

    for i, step in enumerate(task_analysis['steps'], 1):
        yield f"📋 Step {i}/{len(task_analysis['steps'])}: {step['title']}\n"

        # Call appropriate agent
        agent = step['agent']
        yield f"  → Calling {agent} agent...\n"

        result = call_agent(agent, step['prompt'])

        if result["success"]:
            yield f"  ✅ {agent} agent completed\n"
            # Show abbreviated response
            response_preview = result["response"][:100] + "..." if len(result["response"]) > 100 else result["response"]
            yield f"  Response: {response_preview}\n\n"
        else:
            yield f"  ❌ {agent} agent failed: {result['error']}\n\n"

            # Decide whether to continue
            if step['critical']:
                yield "⛔ Critical step failed - stopping workflow\n"
                return
            else:
                yield "⚠️ Non-critical failure - continuing workflow\n\n"

    # Final summary
    yield "✅ Workflow completed successfully!\n"
```

## Streaming Best Practices

### 1. Always Announce Before Acting

```python
# Bad - Silent execution
result = run_command()

# Good - Announce what you're doing
yield "🔧 Running dependency audit...\n"
result = run_command()
yield "✓ Audit complete\n"
```

### 2. Show Progress for Long Operations

```python
# Bad - Silent loop
for file in files:
    process_file(file)

# Good - Show progress
yield f"Processing {len(files)} files...\n"
for i, file in enumerate(files, 1):
    if i % 10 == 0:  # Every 10 files
        yield f"  → Progress: {i}/{len(files)} files\n"
    process_file(file)
yield f"✓ Processed all {len(files)} files\n"
```

### 3. Stream Errors Immediately

```python
# Bad - Return error at end
if error:
    return {"success": False, "error": error}

# Good - Stream error when it happens
if error:
    yield f"❌ Error: {error}\n"
    yield "⏮️ Rolling back changes...\n"
    rollback()
    yield "✓ Rollback complete\n"
    return {"success": False, "rolled_back": True}
```

### 4. Include Next Steps

```python
# Final messages should guide the user
if success:
    yield "✅ Operation successful!\n\n"
    yield "Next steps:\n"
    yield "  1. Run tests to verify changes\n"
    yield "  2. Commit changes with 'git commit'\n"
    yield "  3. Push to remote repository\n"
else:
    yield "❌ Operation failed\n\n"
    yield "To investigate:\n"
    yield "  1. Check error logs above\n"
    yield "  2. Restore from checkpoint if needed\n"
    yield f"  3. Checkpoint ID: {checkpoint_id}\n"
```

### 5. Use Consistent Formatting

```python
# Pattern for all operations:
# 1. Announcement (emoji + description)
# 2. Sub-steps with → prefix
# 3. Completion with ✓ or ❌
# 4. Blank line for readability

yield "🔍 Analyzing codebase...\n"
yield "  → Scanning for dependencies\n"
yield "  → Checking for vulnerabilities\n"
yield "  ✓ Analysis complete\n\n"  # Blank line before next section
```

## Client-Side Display

### Progress Display Example

```
🔍 Starting dependency audit...

  → Detecting package manager (npm/yarn)...
  ✓ Found: npm

📦 Running `npm audit`...

  → Parsing results...
  ✓ Found 3 vulnerabilities

Severity breakdown:
  - High: 2
  - Moderate: 1

🔧 Attempting to fix vulnerabilities...

  → Running npm audit fix...
  ✓ Fixed 2 vulnerabilities
  ⚠️ 1 vulnerability requires manual fix

💾 Creating GitHub issue for manual fix...
  ✓ Issue created: #123

✅ Audit complete!

Summary:
  - Fixed: 2 vulnerabilities
  - Remaining: 1 (tracked in issue #123)
  - Workspace: Clean
```

## Stability Integration

### Critical Operations Must Stream

All critical operations that affect stability must stream progress:

1. **Checkpoint Creation**
```python
yield "💾 Creating checkpoint...\n"
yield "  → Saving git state\n"
yield "  → Backing up package files\n"
yield "  → Running initial tests\n"
yield f"  ✅ Checkpoint: {checkpoint_id}\n\n"
```

2. **Validation**
```python
yield "🔍 Validating environment...\n"
yield "  → Checking git status\n"
yield "  → Verifying tests pass\n"
yield "  → Confirming safe branch\n"
yield "  ✅ Environment safe\n\n"
```

3. **Rollback**
```python
yield "🔄 Rolling back changes...\n"
yield f"  → Restoring checkpoint {checkpoint_id}\n"
yield "  → Reverting file changes\n"
yield "  → Validating rollback\n"
yield "  ✅ Rollback successful\n\n"
```

4. **Session Cleanup**
```python
yield "💾 Archiving session...\n"
yield f"  → Moving {file_count} files to archive\n"
yield "  → Cleaning temporary files\n"
yield "  → Verifying workspace clean\n"
yield "  ✅ Session archived\n\n"
```

## Implementation Checklist

For every new tool or workflow:

- [ ] Announce what you're starting
- [ ] Stream progress for operations >2 seconds
- [ ] Show sub-steps with → prefix
- [ ] Mark completion with ✓ or ❌
- [ ] Stream errors immediately
- [ ] Provide final summary
- [ ] Include next steps or recommendations
- [ ] Use blank lines for readability
- [ ] Test that client can see progress in real-time

## Testing Streaming

### Manual Test

```bash
# Watch progress in real-time
uv run agentcore invoke '{"prompt": "Check dependencies for my project"}' --user-id "test"

# You should see:
# - Each step announced before execution
# - Progress indicators for loops
# - Clear success/failure markers
# - Final summary
```

### Expected Output

```
🔍 Starting dependency check...

  → Detecting package manager...
  ✓ Found: npm

📦 Running audit...
  → Analyzing dependencies...
  ✓ Found 3 vulnerabilities

🔧 Fixing vulnerabilities...
  → [1/3] Fixing lodash...
  ✓ lodash updated
  → [2/3] Fixing minimist...
  ✓ minimist updated
  → [3/3] Fixing axios...
  ❌ axios requires manual fix

💾 Archiving session...
  ✓ Session archived to: .archive/session_20251010_143022

✅ Dependency check complete!
```

## Next Steps

1. **Update All Tools**: Add streaming to every tool function
2. **Test Visibility**: Ensure clients see progress in real-time
3. **Gather Feedback**: Ask developers if progress is clear
4. **Refine Messages**: Improve clarity based on feedback
5. **Document Patterns**: Create library of common progress messages
