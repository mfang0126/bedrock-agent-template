"""Helper utilities for the simplified Planning Agent."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from tools.task_planner import breakdown_task
from common.utils import format_planning_response


def generate_plan(prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return a deterministic task breakdown for the given prompt."""

    return breakdown_task(prompt=prompt, context=context or {})


def format_plan_json(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Generate a plan and return the serialized AgentResponse JSON."""

    plan = generate_plan(prompt, context)
    response = format_planning_response(plan, requirements=prompt)
    return response.to_json()


if __name__ == "__main__":  # pragma: no cover - manual exercise helper
    sample_prompt = "Help me audit the repo vulnerability"
    print(json.dumps(json.loads(format_plan_json(sample_prompt)), indent=2))
