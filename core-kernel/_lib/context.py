"""Build the minimal context passed to one task execution."""

from dataclasses import dataclass
import glob
import hashlib
import json
from pathlib import Path
import re

from .config import configured_tech_contract_paths


FILE_INPUT_RE = re.compile(r"^[^\n]+\.[A-Za-z0-9_-]+(?:\s*#.*)?$")


def _content_digest(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _clean_artifact(value):
    return str(value).strip().strip("`").split("#", 1)[0].strip()


def _module_from_item(item):
    module = str(item.get("module", "")).strip().strip("`")
    if module and module not in {"—", "-"}:
        return module
    target = str(item.get("target", "")).strip().strip("`")
    match = re.search(r"(?:^|/)modules/([^/]+)/", target)
    return match.group(1) if match else ""


def resolve_artifact_path(project_root, feature_dir, item, value, plan_metadata=None):
    """Resolve a file-like contract input; return None for descriptive inputs."""
    clean = _clean_artifact(value)
    if not clean:
        return None
    feature = Path(feature_dir).name
    module = _module_from_item(item)
    if not module and plan_metadata:
        module = str(plan_metadata.get("Base Module", "")).strip()
    target = str(item.get("target", "")).strip().strip("`")
    uses_target = "{target}" in clean
    clean = clean.replace("{feature}", feature).replace("{module}", module).replace("{target}", target)
    if not FILE_INPUT_RE.match(clean):
        return None
    if "{" in clean or "}" in clean:
        return None

    root = Path(project_root)
    context = root / "shiki_context"
    feature_relative = ("modules/", "tests/", "_plan.md", "index.md")
    if uses_target and Path(feature_dir).parent.name == "features" and clean.startswith(feature_relative):
        return Path(feature_dir) / clean
    if clean.startswith("shiki_context/"):
        return root / clean
    if clean.startswith("features/") or clean.startswith("project/") or clean.startswith("modules/"):
        return context / clean
    if clean.startswith("workspace/") or clean.startswith("constitution/"):
        return context / clean
    return root / clean


def expand_artifact_path(path):
    """Expand a contract path pattern without scanning outside its parent."""
    if path is None:
        return ()
    value = str(path)
    if "*" not in value and "?" not in value and "[" not in value:
        return (path,) if path.is_file() else ()
    return tuple(
        candidate
        for candidate in (Path(value) for value in sorted(glob.glob(str(path))))
        if candidate.is_file()
    )


def _resolve_reference(shiki_root, project_root, value):
    clean = _clean_artifact(value)
    if not clean:
        return None
    if clean.startswith("shiki_context/"):
        return Path(project_root) / clean
    path = Path(clean)
    if path.is_absolute():
        return path
    return Path(shiki_root) / clean


@dataclass(frozen=True)
class ContextDocument:
    path: str
    content: str


@dataclass(frozen=True)
class ContextEnvelope:
    task_route: str
    task_context: dict
    contract: dict
    required_artifacts: tuple[ContextDocument, ...]
    rule_documents: tuple[ContextDocument, ...]
    optional_manifest: tuple[str, ...]
    missing_required: tuple[str, ...]

    def render(self):
        public_contract = {
            key: value
            for key, value in self.contract.items()
            if not key.startswith("_") and key not in {"required_inputs", "optional_inputs"}
        }
        parts = [
            "# TaskRoute",
            self.task_route.strip(),
            "",
            "# Task Context",
            "```json",
            json.dumps(self.task_context, ensure_ascii=False, indent=2),
            "```",
            "",
            "# Task Contract",
            "```json",
            json.dumps(public_contract, ensure_ascii=False, indent=2),
            "```",
        ]
        if self.required_artifacts:
            parts.extend(["", "# Required Artifacts"])
            for document in self.required_artifacts:
                parts.extend(
                    [
                        f"## {document.path}",
                        "```text",
                        document.content,
                        "```",
                    ]
                )
        if self.rule_documents:
            parts.extend(["", "# Execution Rules"])
            for document in self.rule_documents:
                parts.extend(
                    [
                        f"## {document.path}",
                        "```text",
                        document.content,
                        "```",
                    ]
                )
        if self.optional_manifest:
            parts.extend(["", "# Optional Manifest"])
            parts.extend(f"- {path}" for path in self.optional_manifest)
        if self.missing_required:
            parts.extend(["", "# Missing Required Artifacts"])
            parts.extend(f"- {path}" for path in self.missing_required)
        return "\n".join(parts).strip() + "\n"


def _document(path, display_path):
    if path is None or not path.is_file():
        return None
    content = path.read_text(encoding="utf-8")
    return ContextDocument(display_path, content)


def _task_context(plan_context, item):
    if plan_context is None:
        return {"current_task": item, "dependencies": []}
    return {
        "plan_path": str(plan_context.path),
        "metadata": {key: value for key, value in plan_context.metadata.items() if value},
        "current_task": item,
        "dependencies": list(plan_context.dependencies_for(item)),
    }


def build_context_envelope(
    shiki_root,
    project_root,
    feature_dir,
    item,
    contract,
    task_route,
    plan_context=None,
):
    """Build a deduplicated envelope for one routed task."""
    required = []
    missing = []
    optional = []
    rules = []
    seen_paths = set()
    seen_content = set()

    def add_document(target, display, collection):
        if target is None:
            return
        canonical = str(target.resolve())
        if canonical in seen_paths:
            return
        document = _document(target, display)
        if document is None:
            return
        seen_paths.add(canonical)
        digest = _content_digest(document.content)
        if digest in seen_content:
            return
        seen_content.add(digest)
        collection.append(document)

    for value in contract.get("required_inputs", []):
        metadata = plan_context.metadata if plan_context is not None else None
        path = resolve_artifact_path(project_root, feature_dir, item, value, plan_metadata=metadata)
        if path is None:
            continue
        if plan_context is not None and path.resolve() == plan_context.path.resolve():
            if not path.is_file():
                missing.append(str(path))
            continue
        matches = expand_artifact_path(path)
        if not matches:
            missing.append(str(path))
            continue
        for match in matches:
            add_document(match, str(match), required)

    for value in contract.get("optional_inputs", []):
        metadata = plan_context.metadata if plan_context is not None else None
        path = resolve_artifact_path(project_root, feature_dir, item, value, plan_metadata=metadata)
        for match in expand_artifact_path(path):
            optional.append(str(match))

    for value in [contract.get("workflow_ref", "")]:
        path = _resolve_reference(shiki_root, project_root, value)
        if path is not None and path.is_file():
            add_document(path, str(value), rules)

    for stack_dir in configured_tech_contract_paths(project_root):
        for path in sorted(stack_dir.glob("*.md")) if stack_dir.is_dir() else []:
            if path.is_file():
                optional.append(str(path))

    team_norm = Path(project_root) / "shiki_context" / "constitution" / "team_norm.md"
    if team_norm.is_file():
        optional.append(str(team_norm))

    optional = tuple(dict.fromkeys(optional))
    return ContextEnvelope(
        task_route=task_route,
        task_context=_task_context(plan_context, item),
        contract=contract,
        required_artifacts=tuple(required),
        rule_documents=tuple(rules),
        optional_manifest=optional,
        missing_required=tuple(missing),
    )
