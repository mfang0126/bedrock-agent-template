"""Async planning tools - submit task and poll for results.

These tools allow long-running operations to execute in background.
User gets task_id immediately, then polls for completion.
"""

import threading
from strands import tool
from src.common.tasks import TaskStore, TaskStatus, get_task_store
from src.tools.planning.plan_generator import (
    generate_implementation_plan,
    parse_requirements,
    validate_plan
)


def _execute_task_in_background(task_store: TaskStore, task_id: str, tool_func, args: dict):
    """Execute tool function in background thread."""
    try:
        task_store.update_status(task_id, TaskStatus.PROCESSING)

        # Execute the actual tool
        result = tool_func(**args)

        task_store.update_status(task_id, TaskStatus.COMPLETED, result=result)

    except Exception as e:
        error_msg = f"Task execution failed: {str(e)}"
        task_store.update_status(task_id, TaskStatus.FAILED, error=error_msg)


@tool
def submit_plan_generation(requirement: str) -> str:
    """Submit implementation plan generation task (async).

    Returns task_id immediately. Use get_task_result() to poll for completion.

    Args:
        requirement: The feature or requirement to plan

    Returns:
        Task ID for polling
    """
    task_store = get_task_store()

    # Create task
    task_id = task_store.create_task(
        tool_name="generate_implementation_plan",
        args={"requirement": requirement}
    )

    # Execute in background
    thread = threading.Thread(
        target=_execute_task_in_background,
        args=(task_store, task_id, generate_implementation_plan, {"requirement": requirement}),
        daemon=True
    )
    thread.start()

    return f"""✅ Plan generation task submitted!

📋 Task ID: {task_id}

Use get_task_result("{task_id}") to check status and retrieve results.

Expected completion: 10-30 seconds (includes retry logic for throttling)"""


@tool
def submit_requirements_parsing(requirements_text: str) -> str:
    """Submit requirements parsing task (async).

    Returns task_id immediately. Use get_task_result() to poll for completion.

    Args:
        requirements_text: Raw requirements or user story

    Returns:
        Task ID for polling
    """
    task_store = get_task_store()

    task_id = task_store.create_task(
        tool_name="parse_requirements",
        args={"requirements_text": requirements_text}
    )

    thread = threading.Thread(
        target=_execute_task_in_background,
        args=(task_store, task_id, parse_requirements, {"requirements_text": requirements_text}),
        daemon=True
    )
    thread.start()

    return f"""✅ Requirements parsing task submitted!

📋 Task ID: {task_id}

Use get_task_result("{task_id}") to check status and retrieve results.

Expected completion: 5-15 seconds"""


@tool
def submit_plan_validation(plan_text: str) -> str:
    """Submit plan validation task (async).

    Returns task_id immediately. Use get_task_result() to poll for completion.

    Args:
        plan_text: The plan to validate

    Returns:
        Task ID for polling
    """
    task_store = get_task_store()

    task_id = task_store.create_task(
        tool_name="validate_plan",
        args={"plan_text": plan_text}
    )

    thread = threading.Thread(
        target=_execute_task_in_background,
        args=(task_store, task_id, validate_plan, {"plan_text": plan_text}),
        daemon=True
    )
    thread.start()

    return f"""✅ Plan validation task submitted!

📋 Task ID: {task_id}

Use get_task_result("{task_id}") to check status and retrieve results.

Expected completion: 5-15 seconds"""


@tool
def get_task_result(task_id: str) -> str:
    """Get task status and result by task ID.

    Poll this tool to check if async task has completed.

    Args:
        task_id: Task ID returned from submit_* functions

    Returns:
        Task status and result (if completed)
    """
    task_store = get_task_store()
    task = task_store.get_task(task_id)

    if not task:
        return f"❌ Task not found: {task_id}\n\nTask may have been cleaned up (tasks expire after 1 hour)."

    status_emoji = {
        TaskStatus.PENDING: "⏳",
        TaskStatus.PROCESSING: "🔄",
        TaskStatus.COMPLETED: "✅",
        TaskStatus.FAILED: "❌"
    }

    emoji = status_emoji.get(task.status, "❓")

    if task.status == TaskStatus.COMPLETED:
        return f"""{emoji} Task Completed!

📋 Task ID: {task_id}
Tool: {task.tool_name}
Status: {task.status.value}

Result:
{task.result}"""

    elif task.status == TaskStatus.FAILED:
        return f"""{emoji} Task Failed

📋 Task ID: {task_id}
Tool: {task.tool_name}
Status: {task.status.value}

Error:
{task.error}

You can retry by submitting a new task."""

    elif task.status == TaskStatus.PROCESSING:
        return f"""{emoji} Task Processing...

📋 Task ID: {task_id}
Tool: {task.tool_name}
Status: {task.status.value}

Please wait and check again in a few seconds."""

    else:  # PENDING
        return f"""{emoji} Task Pending

📋 Task ID: {task_id}
Tool: {task.tool_name}
Status: {task.status.value}

Task queued for execution. Check again in a moment."""
