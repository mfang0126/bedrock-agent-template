"""Simple in-memory task store for async operations.

This is an MVP implementation using in-memory storage.
For production, upgrade to DynamoDB or Redis for persistence.
"""

import uuid
import time
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
import json


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Task metadata and result storage."""
    task_id: str
    status: TaskStatus
    tool_name: str
    args: Dict[str, Any]
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            **asdict(self),
            "status": self.status.value,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "started_at": datetime.fromtimestamp(self.started_at).isoformat() if self.started_at else None,
            "completed_at": datetime.fromtimestamp(self.completed_at).isoformat() if self.completed_at else None,
        }


class TaskStore:
    """In-memory task storage.

    Note: Tasks are lost on agent restart. For production, use DynamoDB.
    """

    def __init__(self):
        self._tasks: Dict[str, Task] = {}

    def create_task(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Create a new task and return task_id.

        Args:
            tool_name: Name of the tool to execute
            args: Tool arguments

        Returns:
            task_id for polling
        """
        task_id = str(uuid.uuid4())
        task = Task(
            task_id=task_id,
            status=TaskStatus.PENDING,
            tool_name=tool_name,
            args=args,
            created_at=time.time()
        )
        self._tasks[task_id] = task
        print(f"📝 Created task {task_id} for {tool_name}")
        return task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self._tasks.get(task_id)

    def update_status(self, task_id: str, status: TaskStatus,
                     result: Optional[str] = None, error: Optional[str] = None):
        """Update task status and result."""
        task = self._tasks.get(task_id)
        if not task:
            return

        task.status = status

        if status == TaskStatus.PROCESSING and not task.started_at:
            task.started_at = time.time()
        elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            task.completed_at = time.time()
            task.result = result
            task.error = error

        print(f"📊 Task {task_id} status: {status.value}")

    def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        """Remove tasks older than max_age_seconds.

        Args:
            max_age_seconds: Maximum age in seconds (default: 1 hour)
        """
        current_time = time.time()
        to_remove = [
            task_id for task_id, task in self._tasks.items()
            if current_time - task.created_at > max_age_seconds
        ]

        for task_id in to_remove:
            del self._tasks[task_id]

        if to_remove:
            print(f"🧹 Cleaned up {len(to_remove)} old tasks")


# Global task store (singleton)
_task_store: Optional[TaskStore] = None


def get_task_store() -> TaskStore:
    """Get global task store instance."""
    global _task_store
    if _task_store is None:
        _task_store = TaskStore()
    return _task_store
