"""Lightweight task planning tools for the Planning Agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    from strands import tool
except ImportError:  # pragma: no cover - strands unavailable in some runtimes
    def tool(func):
        return func


@dataclass
class PlanPhase:
    """Structured phase describing a set of tasks."""

    title: str
    tasks: List[str]
    duration: str = "unspecified"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "tasks": self.tasks,
            "duration": self.duration,
        }


_DEFAULT_PHASES: Dict[str, List[PlanPhase]] = {
    "security": [
        PlanPhase("Establish Scope", [
            "Confirm target repository and environments",
            "Identify package managers and lockfiles",
            "Gather recent security reports or audits",
        ], "0.5 day"),
        PlanPhase("Inventory Dependencies", [
            "Install tooling (yarn/npm/pnpm, osv, snyk, etc.)",
            "Generate dependency graphs and SBOM if available",
            "Highlight high-risk runtime and build dependencies",
        ], "0.5 day"),
        PlanPhase("Automated Scanning", [
            "Run npm/yarn audit with JSON output",
            "Execute SAST tooling (CodeQL/Semgrep) if configured",
            "Check container or infrastructure manifests",
        ], "1 day"),
        PlanPhase("Manual Review", [
            "Prioritize critical findings and map to owners",
            "Spot-check custom authentication/authorization code",
            "Document mitigation options for each high severity item",
        ], "1 day"),
        PlanPhase("Remediation & Verification", [
            "Schedule dependency upgrades or patches",
            "Add regression tests or monitoring hooks",
            "Re-run audit tooling to confirm clean results",
        ], "1 day"),
        PlanPhase("Reporting", [
            "Summarize findings, status, and mitigation timeline",
            "Share follow-up actions with engineering stakeholders",
            "Archive audit artifacts for compliance",
        ], "0.5 day"),
    ],
    "feature": [
        PlanPhase("Clarify Requirements", [
            "Confirm success criteria and target personas",
            "List must-have versus optional behaviours",
            "Capture non-functional constraints (perf/accessibility)",
        ], "0.5 day"),
        PlanPhase("Design Solution", [
            "Create high-level architecture or UI sketch",
            "Review integration points and data contracts",
            "Identify dependencies or blockers",
        ], "1 day"),
        PlanPhase("Implementation", [
            "Set up feature branch and scaffolding",
            "Implement core components with incremental commits",
            "Pair review on risky changes",
        ], "2-3 days"),
        PlanPhase("Validation", [
            "Add unit/integration tests",
            "Run regression suite or smoke tests",
            "Update documentation and changelog",
        ], "1 day"),
    ],
}


def _select_phases(prompt: str) -> List[PlanPhase]:
    prompt_lower = prompt.lower()
    if any(token in prompt_lower for token in ["audit", "security", "vulnerability", "risk"]):
        return _DEFAULT_PHASES["security"]
    return _DEFAULT_PHASES["feature"]


def _infer_dependencies(prompt: str) -> List[str]:
    prompt_lower = prompt.lower()
    dependencies = []
    if "frontend" in prompt_lower or "ui" in prompt_lower:
        dependencies.append("UI component library access")
    if "database" in prompt_lower or "sql" in prompt_lower:
        dependencies.append("Database credentials / migration tooling")
    if "audit" in prompt_lower or "security" in prompt_lower:
        dependencies.append("Security scanning tooling access")
        dependencies.append("Credentialed access to CI and package registry")
    if "mobile" in prompt_lower:
        dependencies.append("Mobile build signing certificates")
    if not dependencies:
        dependencies.append("Clarified scope and success criteria")
    return dependencies


def _estimate_effort(phases: List[PlanPhase]) -> str:
    durations = [phase.duration for phase in phases if phase.duration != "unspecified"]
    if not durations:
        return "3-4 days"
    # Rough categorical estimate: treat each phase as a day or fractional day.
    effort_points = 0.0
    for duration in durations:
        if "0.5" in duration:
            effort_points += 0.5
        elif "2-3" in duration:
            effort_points += 2.5
        elif "1" in duration:
            effort_points += 1
        else:
            effort_points += 1
    if effort_points <= 2:
        return "1-2 days"
    if effort_points <= 4:
        return "3-4 days"
    return "1+ week"


@tool
def breakdown_task(prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Produce a lightweight implementation plan for the orchestrator."""

    context = context or {}
    phases = _select_phases(prompt)
    dependencies = _infer_dependencies(prompt)
    effort = _estimate_effort(phases)

    plan = {
        "title": context.get("title") or "Task Plan",
        "summary": f"Breakdown for: {prompt.strip()[:120]}",
        "phases": [phase.to_dict() for phase in phases],
        "dependencies": dependencies,
        "risk_level": "Medium" if "audit" in prompt.lower() else "Low",
        "estimated_effort": effort,
    }

    return plan
