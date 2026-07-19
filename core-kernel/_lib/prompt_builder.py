"""Build provider prompts around one deterministic Shiki Context Envelope."""

COMMAND_INSTRUCTIONS = {
    "status": "Read active_task, the current Plan, artifacts, and the latest result. Report the current phase, ready or recovery task, gates, and blockers. Do not modify files.",
    "next": "Execute only the selected task in the Context Envelope. After Workflow verification, call the Kernel completion tool: use `shiki task complete <task_id>` for a fixed output, add `--output <path>` for each major output of a flexible code task, or use `--noop <reason>` when no change is required. Use `shiki plan add-item` only for a narrow Plan expansion. Execute exactly one task.",
    "review": "Review the current task or phase without editing. Check outputs, design/implementation alignment, project constraints, and risk. Return CHANGE_REQUEST when work is not acceptable. In CLI automatic mode the Orchestrator stops; in Prompt manual mode the developer chooses the next action.",
    "modify": "Modify only the user-authorized fact source and update the related Plan focus. Do not cascade into unrequested downstream work.",
    "sync": "Execute one ready Code-to-Spec item from workspace/sync_plan.md. Create the bounded Plan when it is absent; otherwise apply exactly one item.",
    "fix": "Diagnose the supplied failure against direct source and specs. Make a local fix only when authorized; route spec drift to sync or a feature change.",
    "test": "Plan or add tests for the selected feature, module, or entrance. Keep the current Plan as the task ledger and do not scan the whole source tree.",
    "doctor": "Diagnose Shiki structure, Plan, index, and migration problems. Stay read-only until the developer explicitly authorizes one ready doctor item.",
    "flow": "Generate or update the explicitly requested business flow and scenario diagram as an optional review artifact.",
}

VALID_TASK_STATUSES = ("PASS", "BLOCKED", "FAILED", "MANUAL_DECISION")
VALID_REVIEW_STATUSES = VALID_TASK_STATUSES + ("CHANGE_REQUEST",)


def build_execution_prompt(command, user_tail="", envelope=None):
    """Render one provider-facing prompt with a stable status protocol."""
    instruction = COMMAND_INSTRUCTIONS.get(command)
    if instruction is None:
        raise ValueError(f"unsupported Shiki prompt command: {command}")

    sections = [
        "# Shiki Execution Boundary",
        "",
        "- Core Kernel already owns routing, completion semantics, and the execution boundary.",
        "- Read only this prompt's Context Envelope and optional paths needed by the task.",
        "- Keep edits within the selected target, Workflow, and user scope.",
        "- Return BLOCKED or MANUAL_DECISION when required input is missing, ownership is ambiguous, or scope must expand.",
        "",
        "# Command",
        "",
        instruction,
    ]
    if user_tail.strip():
        sections.extend(["", "# User Scope", "", user_tail.strip()])
    if envelope is not None:
        sections.extend(["", "# Context Envelope", "", envelope.render().rstrip()])

    statuses = ", ".join(VALID_REVIEW_STATUSES if command == "review" else VALID_TASK_STATUSES)
    sections.extend(
        [
            "",
            "# Result Protocol",
            "",
            "The first non-empty line must be `<STATUS>: <summary>`; do not put a heading, list, or code block before it.",
            f"`STATUS` must be one of: {statuses}.",
            "Continue with developer-facing Markdown covering the task, outputs or findings, verification, Plan/active-task updates, and the recommended next action.",
            "`BLOCKED`, `FAILED`, `MANUAL_DECISION`, and `CHANGE_REQUEST` must never be written to `_plan.md.output_files`.",
        ]
    )
    return "\n".join(sections).strip() + "\n"
