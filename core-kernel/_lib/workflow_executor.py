"""Workflow-executor abstraction for routed Shiki tasks.

Runner/kernel decides *what* the next item is.
Workflow executors decide *how* to execute that one item by consuming the routed
task contract and its referenced workflow.

This module intentionally defines only the interface layer so future CLI,
provider and prompt runners can share one execution shape.
"""

from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class WorkflowExecutionPlan:
    """Execution-time view of one routed task."""

    task_id: str
    stage: str
    workflow_ref: str
    tech_contract: str
    artifact_path: str
    artifact_mode: str
    template_ref: str
    inputs: tuple[str, ...]
    references: tuple[str, ...]
    checks: tuple[str, ...]
    evidence_rules: tuple[str, ...]
    done_condition: tuple[str, ...]


def build_execution_plan(item, contract):
    """Build a workflow execution plan from one plan item and task contract."""
    artifact = contract["artifact"]
    return WorkflowExecutionPlan(
        task_id=contract["id"],
        stage=contract["stage"],
        workflow_ref=contract["workflow_ref"],
        tech_contract=contract["tech_contract"],
        artifact_path=artifact["path"],
        artifact_mode=artifact["mode"],
        template_ref=artifact["template"],
        inputs=tuple(contract["inputs"]),
        references=tuple(contract["references"]),
        checks=tuple(contract["checks"]),
        evidence_rules=tuple(contract["evidence_rules"]),
        done_condition=tuple(contract["done_condition"]),
    )


@dataclass(frozen=True)
class WorkflowExecutionResult:
    """Minimal normalized result returned by a workflow executor."""

    status: Literal["completed", "blocked", "failed"]
    summary: str
    modified_files: tuple[str, ...] = ()
    blocker: str = ""


class WorkflowExecutor(Protocol):
    """Interface implemented by prompt runners, CLI runners or providers."""

    def execute(self, plan: WorkflowExecutionPlan) -> WorkflowExecutionResult:
        """Execute exactly one workflow plan and return a normalized result."""

