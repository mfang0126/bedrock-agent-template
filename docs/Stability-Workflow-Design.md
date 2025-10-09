# Stability Workflow Design for Multi-Agent Development System

## Executive Summary

This document outlines system prompt optimizations and stability workflows to ensure our multi-agent system runs reliably for developers. The key principle: **Validate → Execute → Verify → Rollback if needed**.

---

## 1. Current System Prompt Analysis

### Issues Identified

#### Coding Agent
**Current Weakness**: No pre-execution validation
```python
# Current: Executes directly without safety checks
@tool
def execute_command(command: str, timeout: int = 30):
    # Runs command immediately - RISKY
```

**Problem**: Could break production code, delete files, run dangerous commands

#### Planning Agent
**Current Weakness**: No feasibility validation
```python
# Current: Creates plans without checking resources
def breakdown_task(prompt: str):
    # Returns plan without validating if it's achievable
```

**Problem**: Plans might be impossible to execute given current environment

#### Orchestrator Agent
**Current Weakness**: No rollback mechanism
```python
# Current: Sequential execution with no checkpoint/rollback
def orchestrate_task(task: str):
    # Executes step 1, 2, 3... if step 2 fails, step 1 changes are permanent
```

**Problem**: Partial failures leave system in inconsistent state

---

## 2. Proposed System Prompt Improvements

### 2.1 Coding Agent - Add Safety-First Mindset

**New System Prompt Additions**:
```
You are a coding assistant with SAFETY-FIRST principles:

BEFORE executing ANY command:
1. Analyze the command for potential risks:
   - File deletion (rm, del, unlink)
   - System modification (chmod, chown, kill)
   - Network operations (curl, wget, git push)
   - Package changes (npm install, pip install)

2. Create a safety checkpoint:
   - List affected files
   - Show what will be modified
   - Ask for confirmation for HIGH-RISK operations

3. Validate the environment:
   - Check if required dependencies exist
   - Verify file paths are within workspace
   - Ensure adequate disk space/permissions

AFTER executing commands:
1. Verify the outcome matches expectations
2. Run validation tests
3. Report success/failure with details

AT END OF SESSION:
1. Archive session work automatically:
   - Move all created/modified files to .archive/session_YYYYMMDD_HHMMSS/
   - Clean up temporary files (*.tmp, *.log, __pycache__, etc.)
   - Create session summary for future reference
   - Verify workspace is clean

2. Provide session report:
   - What was accomplished
   - Files archived
   - Any warnings or issues
   - Workspace state (clean/needs attention)

HIGH-RISK operations requiring confirmation:
- Any command with 'rm -rf'
- Package installations in production
- Git operations affecting remote branches
- Database migrations
- System configuration changes

Tools available for safety:
- execute_command_with_preview: Show what will happen before executing
- execute_with_rollback: Create checkpoint and allow rollback
- validate_environment: Check if environment is ready
```

### 2.2 Planning Agent - Add Feasibility Validation

**New System Prompt Additions**:
```
You are a planning assistant with FEASIBILITY-FIRST principles:

BEFORE creating a plan:
1. Assess available resources:
   - Developer skill level
   - Time constraints
   - Technology stack compatibility
   - Required dependencies

2. Validate each phase:
   - Can this phase be tested independently?
   - Are there clear success criteria?
   - What are the dependencies?
   - What could go wrong?

3. Include validation checkpoints:
   - After each phase, what should be verified?
   - How do we know if the phase succeeded?
   - What are the rollback steps?

Plan structure MUST include:
- Risk assessment for each phase
- Validation criteria
- Rollback procedures
- Estimated effort with confidence level
- Alternative approaches for high-risk phases
```

### 2.3 Orchestrator Agent - Add Workflow Safety

**New System Prompt Additions**:
```
You are an orchestrator with RELIABILITY-FIRST principles:

BEFORE executing a workflow:
1. Create execution plan:
   - List all steps with dependencies
   - Identify rollback points
   - Estimate total time
   - Highlight risky operations

2. Validate workflow:
   - Can we recover from each step's failure?
   - Are there circular dependencies?
   - Do we have required agent access?

3. Create checkpoints:
   - Save state before each agent call
   - Allow manual intervention for risky steps
   - Provide progress updates

DURING workflow execution:
- Update status after each agent call
- Stop on critical failures
- Continue on non-critical failures with warnings
- Log all agent communications

AFTER workflow completion:
- Validate all steps succeeded
- Run smoke tests if available
- Report comprehensive status
- Suggest next steps or required fixes
```

---

## 3. Stability Workflows to Add

### Workflow 1: Pre-Flight Validation Workflow

**Purpose**: Validate environment before making any changes

```yaml
Workflow: pre_flight_validation
Trigger: Before any code modification
Steps:
  1. Environment Check:
     - Git status (clean working directory?)
     - Current branch (not main/master?)
     - Dependencies installed?
     - Tests passing?

  2. Risk Assessment:
     - What will be modified?
     - Can changes be rolled back?
     - Are there adequate tests?

  3. Checkpoint Creation:
     - Create git stash or commit
     - Save current state
     - Document baseline

Output: GO/NO-GO decision with reasons
```

**Implementation**: New tool for Orchestrator
```python
@tool
def validate_environment(operation_type: str, affected_files: List[str]) -> Dict:
    """Pre-flight checks before executing operations."""
    checks = {
        "git_status": check_git_clean(),
        "branch_safety": check_not_on_main(),
        "dependencies": check_dependencies_installed(),
        "tests_passing": run_quick_tests(),
        "disk_space": check_disk_space(),
    }

    risk_level = assess_risk(operation_type, affected_files)

    return {
        "safe_to_proceed": all(checks.values()) and risk_level < 0.7,
        "checks": checks,
        "risk_level": risk_level,
        "recommendations": generate_recommendations(checks, risk_level)
    }
```

### Workflow 2: Staged Execution with Validation

**Purpose**: Execute operations in stages with validation gates

```yaml
Workflow: staged_execution
Steps:
  1. Plan Phase:
     Planning Agent: Create execution plan

  2. Validation Phase:
     Developer: Review and approve plan

  3. Execution Phase (for each step):
     a. Create checkpoint
     b. Execute step
     c. Validate outcome
     d. If validation fails:
        - Stop execution
        - Show failure details
        - Offer rollback

  4. Verification Phase:
     - Run full test suite
     - Check for regressions
     - Validate integration

  5. Completion Phase:
     - Commit changes
     - Update tracking (Jira/GitHub)
     - Document what was done
```

**Implementation**: Enhanced Orchestrator workflow
```python
@tool
def execute_staged_workflow(
    plan: Dict,
    validation_mode: str = "auto"  # auto, manual, skip
) -> Dict:
    """Execute workflow with validation gates."""

    checkpoints = []
    results = []

    for phase in plan["phases"]:
        # Create checkpoint
        checkpoint_id = create_checkpoint()
        checkpoints.append(checkpoint_id)

        # Execute phase
        result = execute_phase(phase)
        results.append(result)

        # Validate
        validation = validate_phase_outcome(phase, result)

        if not validation["passed"]:
            # Validation failed - stop here
            return {
                "status": "failed",
                "phase": phase["title"],
                "error": validation["error"],
                "checkpoint": checkpoint_id,
                "rollback_available": True,
                "rollback_command": f"rollback_to_checkpoint({checkpoint_id})"
            }

        # Ask for approval if manual mode
        if validation_mode == "manual":
            approval = ask_for_approval(phase, result, validation)
            if not approval:
                return {
                    "status": "cancelled_by_user",
                    "checkpoint": checkpoint_id
                }

    # All phases succeeded
    return {
        "status": "success",
        "results": results,
        "checkpoints_created": len(checkpoints)
    }
```

### Workflow 3: Continuous Validation Workflow

**Purpose**: Run tests continuously as changes are made

```yaml
Workflow: continuous_validation
Trigger: After each file modification
Steps:
  1. Fast Feedback:
     - Lint modified files
     - Run unit tests for modified code
     - Check type safety

  2. Impact Analysis:
     - Find dependent code
     - Run integration tests for affected modules

  3. Regression Check:
     - Run critical path tests
     - Verify core functionality unchanged

  4. Report:
     - Show what broke
     - Suggest fixes
     - Offer to revert if needed
```

**Implementation**: New Coding Agent capability
```python
@tool
def continuous_validation(
    modified_files: List[str],
    validation_level: str = "standard"  # quick, standard, comprehensive
) -> Dict:
    """Run validation checks on modified code."""

    results = {}

    # Level 1: Fast feedback (< 5 seconds)
    results["lint"] = run_linter(modified_files)
    results["types"] = check_types(modified_files)

    if validation_level in ["standard", "comprehensive"]:
        # Level 2: Unit tests (< 30 seconds)
        results["unit_tests"] = run_unit_tests_for_files(modified_files)

    if validation_level == "comprehensive":
        # Level 3: Integration tests (< 2 minutes)
        results["integration_tests"] = run_integration_tests()
        results["regression"] = run_critical_path_tests()

    # Aggregate results
    all_passed = all(r.get("passed", True) for r in results.values())

    return {
        "all_passed": all_passed,
        "results": results,
        "recommendation": "proceed" if all_passed else "fix_issues",
        "failures": [k for k, v in results.items() if not v.get("passed", True)]
    }
```

### Workflow 4: Rollback and Recovery Workflow

**Purpose**: Gracefully recover from failures

```yaml
Workflow: rollback_recovery
Trigger: When operation fails or user requests rollback
Steps:
  1. Assess Damage:
     - What changed since last checkpoint?
     - What's currently broken?
     - Can we rollback safely?

  2. Create Safety Backup:
     - Backup current state (even if broken)
     - User might want to investigate later

  3. Rollback:
     - Restore to last known good state
     - Verify rollback succeeded

  4. Validate Recovery:
     - Run tests to confirm system is stable
     - Check for data loss

  5. Analyze Failure:
     - What went wrong?
     - How can we prevent this?
     - Document the issue
```

**Implementation**: Orchestrator recovery tool
```python
@tool
def rollback_to_checkpoint(
    checkpoint_id: str,
    backup_current: bool = True
) -> Dict:
    """Rollback to a previous checkpoint."""

    # Backup current state
    if backup_current:
        backup_id = create_backup("pre_rollback_" + datetime.now().isoformat())

    # Get checkpoint data
    checkpoint = load_checkpoint(checkpoint_id)

    # Restore files
    restore_results = restore_files(checkpoint["files"])

    # Restore git state if needed
    if checkpoint.get("git_commit"):
        git_results = git_reset_to(checkpoint["git_commit"])

    # Validate restoration
    validation = validate_system_state()

    return {
        "rollback_successful": validation["healthy"],
        "checkpoint_id": checkpoint_id,
        "backup_id": backup_id if backup_current else None,
        "files_restored": len(restore_results),
        "validation": validation,
        "next_steps": [
            "Run tests to verify stability",
            "Investigate what caused the failure",
            "Fix the issue before retrying"
        ]
    }
```

### Workflow 5: Session Cleanup and Archiving

**Purpose**: Clean up workspace after each session and archive work for future reference

```yaml
Workflow: session_cleanup
Trigger: End of each session or workflow completion
Steps:
  1. Identify Session Work:
     - List files created during session
     - Find temporary files and directories
     - Identify logs and outputs

  2. Archive Session:
     - Create archive folder: .archive/session_YYYYMMDD_HHMMSS/
     - Move all session files to archive
     - Preserve directory structure
     - Create session summary

  3. Clean Workspace:
     - Remove temporary files
     - Delete empty directories
     - Reset to clean state

  4. Update Session Log:
     - Record what was accomplished
     - List archived files
     - Note any issues or warnings

  5. Verify Cleanup:
     - Ensure workspace is clean
     - Confirm critical files not deleted
     - Test that project still works
```

**Implementation**: New Coding Agent tool
```python
@tool
def archive_session_work(
    session_id: str = None,
    cleanup_temp: bool = True
) -> Dict[str, Any]:
    """Archive session work and clean up workspace."""

    import shutil
    from datetime import datetime

    # Generate session ID if not provided
    if not session_id:
        session_id = datetime.now().strftime("session_%Y%m%d_%H%M%S")

    workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
    archive_root = os.path.join(workspace_root, '.archive')
    session_archive = os.path.join(archive_root, session_id)

    # Create archive directory
    os.makedirs(session_archive, exist_ok=True)

    # Track what we archive
    archived_files = []
    temp_files_removed = []

    # Step 1: Identify session work
    session_files = identify_session_files(workspace_root)

    # Step 2: Archive session files
    for file_path in session_files:
        if os.path.exists(file_path):
            # Preserve directory structure
            rel_path = os.path.relpath(file_path, workspace_root)
            archive_path = os.path.join(session_archive, rel_path)

            # Create parent directories
            os.makedirs(os.path.dirname(archive_path), exist_ok=True)

            # Move file to archive
            shutil.move(file_path, archive_path)
            archived_files.append(rel_path)

    # Step 3: Clean temporary files
    if cleanup_temp:
        temp_patterns = [
            "*.tmp", "*.temp", "*.log",
            "__pycache__", "*.pyc", ".pytest_cache",
            "node_modules/.cache", ".DS_Store"
        ]

        for pattern in temp_patterns:
            temp_files = glob.glob(
                os.path.join(workspace_root, "**", pattern),
                recursive=True
            )
            for temp_file in temp_files:
                # Don't delete files in archive
                if not temp_file.startswith(archive_root):
                    if os.path.isfile(temp_file):
                        os.remove(temp_file)
                        temp_files_removed.append(temp_file)
                    elif os.path.isdir(temp_file):
                        shutil.rmtree(temp_file)
                        temp_files_removed.append(temp_file)

    # Step 4: Create session summary
    summary = {
        "session_id": session_id,
        "archived_at": datetime.now().isoformat(),
        "files_archived": len(archived_files),
        "temp_files_removed": len(temp_files_removed),
        "archive_location": session_archive,
        "workspace_state": "clean"
    }

    summary_path = os.path.join(session_archive, "session_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    # Step 5: Verify cleanup
    verification = verify_workspace_clean(workspace_root, archive_root)

    return {
        "success": True,
        "session_id": session_id,
        "archived_files": archived_files[:10],  # First 10 for preview
        "total_archived": len(archived_files),
        "temp_files_removed": len(temp_files_removed),
        "archive_location": session_archive,
        "workspace_clean": verification["clean"],
        "message": f"Session archived to {session_archive}. Workspace cleaned."
    }


def identify_session_files(workspace_root: str) -> List[str]:
    """Identify files created or modified in current session."""

    # Get all files in workspace
    all_files = []
    for root, dirs, files in os.walk(workspace_root):
        # Skip archive directory
        if '.archive' in root:
            continue

        for file in files:
            file_path = os.path.join(root, file)
            all_files.append(file_path)

    # Filter to recent files (modified in last session)
    # For now, we'll archive all non-archive files
    # In production, could track session start time and filter by mtime

    return all_files


def verify_workspace_clean(workspace_root: str, archive_root: str) -> Dict[str, Any]:
    """Verify workspace is in clean state."""

    # Count remaining files (excluding archive)
    remaining_files = []
    for root, dirs, files in os.walk(workspace_root):
        if '.archive' in root:
            continue
        for file in files:
            remaining_files.append(os.path.join(root, file))

    # Check for common temp files
    temp_files_exist = any(
        f.endswith(('.tmp', '.temp', '.log'))
        for f in remaining_files
    )

    return {
        "clean": not temp_files_exist,
        "remaining_files": len(remaining_files),
        "temp_files_exist": temp_files_exist
    }


@tool
def list_archived_sessions() -> Dict[str, Any]:
    """List all archived sessions."""

    workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
    archive_root = os.path.join(workspace_root, '.archive')

    if not os.path.exists(archive_root):
        return {
            "success": True,
            "sessions": [],
            "message": "No archived sessions found"
        }

    sessions = []
    for session_dir in os.listdir(archive_root):
        session_path = os.path.join(archive_root, session_dir)
        if os.path.isdir(session_path):
            # Try to read summary
            summary_path = os.path.join(session_path, "session_summary.json")
            if os.path.exists(summary_path):
                with open(summary_path) as f:
                    summary = json.load(f)
                    sessions.append(summary)
            else:
                sessions.append({
                    "session_id": session_dir,
                    "archive_location": session_path
                })

    return {
        "success": True,
        "sessions": sessions,
        "total_sessions": len(sessions),
        "message": f"Found {len(sessions)} archived sessions"
    }


@tool
def restore_session(session_id: str) -> Dict[str, Any]:
    """Restore files from an archived session."""

    workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
    archive_root = os.path.join(workspace_root, '.archive')
    session_archive = os.path.join(archive_root, session_id)

    if not os.path.exists(session_archive):
        return {
            "success": False,
            "error": f"Session {session_id} not found",
            "message": "Session does not exist"
        }

    # Restore files
    restored_files = []
    for root, dirs, files in os.walk(session_archive):
        for file in files:
            if file == "session_summary.json":
                continue

            archive_path = os.path.join(root, file)
            rel_path = os.path.relpath(archive_path, session_archive)
            restore_path = os.path.join(workspace_root, rel_path)

            # Create parent directories
            os.makedirs(os.path.dirname(restore_path), exist_ok=True)

            # Copy file (don't move - keep archive intact)
            shutil.copy2(archive_path, restore_path)
            restored_files.append(rel_path)

    return {
        "success": True,
        "session_id": session_id,
        "files_restored": restored_files[:10],
        "total_restored": len(restored_files),
        "message": f"Restored {len(restored_files)} files from {session_id}"
    }
```

### Workflow 6: Dependency Management Safety Workflow

**Purpose**: Safely manage dependencies without breaking the project

```yaml
Workflow: safe_dependency_update
Steps:
  1. Pre-Update Snapshot:
     - Record current dependencies
     - Run full test suite
     - Create checkpoint

  2. Analyze Update Impact:
     - Check for breaking changes
     - Review changelogs
     - Assess risk level

  3. Isolated Testing:
     - Update in test environment
     - Run all tests
     - Check for failures

  4. If Tests Pass:
     - Apply to main codebase
     - Run tests again
     - Monitor for issues

  5. If Tests Fail:
     - Rollback immediately
     - Create GitHub issue with details
     - Suggest manual review
```

**Implementation**: Enhanced Coding Agent workflow
```python
@tool
def safe_dependency_update(
    packages: List[str],
    update_type: str = "patch"  # patch, minor, major
) -> Dict:
    """Safely update dependencies with validation."""

    # Step 1: Create snapshot
    snapshot = {
        "dependencies": read_package_json(),
        "lockfile": read_lockfile(),
        "test_results": run_all_tests()
    }
    checkpoint_id = save_checkpoint(snapshot)

    # Step 2: Analyze impact
    impact = analyze_dependency_impact(packages, update_type)

    if impact["risk_level"] > 0.7:
        return {
            "status": "blocked",
            "reason": "High risk updates require manual review",
            "impact": impact,
            "recommendation": "Review breaking changes before proceeding"
        }

    # Step 3: Execute update
    update_result = execute_dependency_update(packages, update_type)

    # Step 4: Validate
    validation_result = run_all_tests()

    if not validation_result["all_passed"]:
        # Rollback
        rollback_to_checkpoint(checkpoint_id)

        return {
            "status": "failed",
            "rolled_back": True,
            "failures": validation_result["failures"],
            "recommendation": "Manual investigation required",
            "github_issue": create_dependency_issue(packages, validation_result)
        }

    # Success
    return {
        "status": "success",
        "packages_updated": packages,
        "checkpoint_id": checkpoint_id,
        "test_results": validation_result
    }
```

---

## 4. New Tools to Add

### For Coding Agent:

1. **`validate_environment`** - Pre-flight environment checks
2. **`create_checkpoint`** - Save current state for rollback
3. **`rollback_to_checkpoint`** - Restore previous state
4. **`execute_with_preview`** - Show what will happen before executing
5. **`continuous_validation`** - Run tests on modified code
6. **`safe_dependency_update`** - Update dependencies with validation
7. **`archive_session_work`** - Archive session files and clean workspace ✨ NEW
8. **`list_archived_sessions`** - List all archived sessions ✨ NEW
9. **`restore_session`** - Restore files from archived session ✨ NEW

### For Planning Agent:

1. **`validate_plan_feasibility`** - Check if plan is achievable
2. **`assess_plan_risks`** - Identify potential issues
3. **`generate_rollback_plan`** - Create recovery procedures

### For Orchestrator Agent:

1. **`pre_flight_validation`** - Validate before workflow execution
2. **`execute_staged_workflow`** - Execute with validation gates
3. **`rollback_workflow`** - Recover from failures
4. **`monitor_workflow_health`** - Track workflow status

### For GitHub Agent:

1. **`create_safety_branch`** - Create branch with checkpoint
2. **`validate_before_merge`** - Check tests before merging
3. **`create_failure_issue`** - Auto-create issue on failures

---

## 5. Implementation Priority

### Phase 1: Critical Safety & Cleanup (Week 1)
- [ ] Add `validate_environment` to Coding Agent
- [ ] Add `create_checkpoint` and `rollback_to_checkpoint`
- [ ] Add `archive_session_work`, `list_archived_sessions`, `restore_session` ✨ NEW
- [ ] Update Coding Agent system prompt to auto-archive at session end ✨ NEW
- [ ] Update Orchestrator system prompt with safety-first principles
- [ ] Add pre-flight validation to Orchestrator

### Phase 2: Validation Workflows (Week 2)
- [ ] Implement `continuous_validation` in Coding Agent
- [ ] Add `execute_staged_workflow` to Orchestrator
- [ ] Update Planning Agent system prompt with feasibility checks
- [ ] Add `validate_plan_feasibility` to Planning Agent

### Phase 3: Recovery Mechanisms (Week 3)
- [ ] Implement full rollback workflow in Orchestrator
- [ ] Add `safe_dependency_update` to Coding Agent
- [ ] Add failure issue creation to GitHub Agent
- [ ] Integrate all workflows into Orchestrator

### Phase 4: Testing & Refinement (Week 4)
- [ ] Test all workflows end-to-end
- [ ] Document workflow usage
- [ ] Create example scenarios
- [ ] Gather feedback and iterate

---

## 6. Success Metrics

### Stability Metrics
- **Rollback Success Rate**: >95% of rollbacks should restore working state
- **Pre-Flight Catch Rate**: >80% of risky operations should be caught before execution
- **Test Pass Rate**: >90% of changes should pass continuous validation
- **Recovery Time**: <2 minutes to rollback from failure

### Developer Experience Metrics
- **Confidence Level**: Developers feel safe making changes
- **Interruption Rate**: <10% of workflows should require manual intervention
- **Time to Safety**: <30 seconds for environment validation
- **Clarity of Errors**: 100% of errors should provide actionable guidance

---

## 7. Example: Complete Safe Workflow

```python
# Developer request: "Update dependencies and fix vulnerabilities"

# Step 1: Orchestrator analyzes request
orchestrator.analyze_task("Update dependencies and fix vulnerabilities")
# → Detects: Dependency management task
# → Agents needed: Coding, GitHub, Jira

# Step 2: Pre-flight validation
validation = orchestrator.pre_flight_validation({
    "operation": "dependency_update",
    "affected_files": ["package.json", "package-lock.json"]
})
# → Checks: Git clean? Tests passing? On safe branch?
# → Result: SAFE TO PROCEED

# Step 3: Create safety checkpoint
checkpoint = coding_agent.create_checkpoint()
# → Saves: Current dependencies, test results, git state
# → Checkpoint ID: ckpt_20251010_123456

# Step 4: Execute with staged validation
result = coding_agent.safe_dependency_update(
    packages=["all"],
    update_type="patch"
)

# If successful:
# → Tests passed
# → Dependencies updated
# → Checkpoint kept for 24h

# If failed:
# → Automatic rollback
# → GitHub issue created
# → Jira ticket updated with blocker status
# → Developer notified with details

# Step 5: Continuous monitoring
orchestrator.monitor_workflow_health()
# → Tracks: Memory usage, test results, error rates
# → Alerts: If anything degrades post-update
```

---

## 8. Conclusion

**Key Principle**: Every operation should be **Validatable, Executable, Verifiable, and Reversible**.

By implementing these workflows and system prompt improvements, we create a multi-agent system that developers can trust with their codebase. The system becomes not just powerful, but also safe and predictable.

**Next Step**: Implement Phase 1 (Critical Safety) this week to establish the foundation for stable operations.
