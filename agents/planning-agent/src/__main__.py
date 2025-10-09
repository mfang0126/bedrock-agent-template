"""CLI entry for the simplified Planning Agent (argparse-based)."""

import argparse
import json
import sys
from pathlib import Path

try:
    from .agent import format_plan_json
except ImportError:  # pragma: no cover - script executed directly
    sys.path.insert(0, str(Path(__file__).parent))
    from agent import format_plan_json  # type: ignore


def main() -> None:
    parser = argparse.ArgumentParser(description="Planning Agent - task breakdown helper")
    parser.add_argument("prompt", help="Goal or requirement to break into steps")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Emit raw JSON string without pretty-printing",
    )
    args = parser.parse_args()

    response_json = format_plan_json(args.prompt)
    if args.raw:
        print(response_json)
    else:
        print(json.dumps(json.loads(response_json), indent=2))


if __name__ == "__main__":
    main()
