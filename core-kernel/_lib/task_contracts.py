"""Machine-readable task contract loader.

Task contracts are stored as YAML for human readability. Runtime loading prefers
PyYAML when available and falls back to a tiny parser that supports the limited
subset used by Shiki task contracts.
"""

import ast
from dataclasses import dataclass

from .paths import get_shiki_root


CANONICAL_REQUIRED_FIELDS = (
    "kind",
    "id",
    "stage",
    "goal",
    "inputs",
    "workflow_ref",
)

ALIAS_REQUIRED_FIELDS = ("kind", "id", "canonical")
CANONICAL_ALLOWED_FIELDS = set(CANONICAL_REQUIRED_FIELDS) | {"output"}
ALIAS_ALLOWED_FIELDS = set(ALIAS_REQUIRED_FIELDS) | {"bindings"}

@dataclass(frozen=True)
class ProducerRecommendation:
    missing_artifact: str
    producers: tuple[str, ...]

    @property
    def status(self):
        if len(self.producers) == 1:
            return "recommended"
        if self.producers:
            return "manual_decision"
        return "blocked"

    @property
    def recommended_contract(self):
        return self.producers[0] if len(self.producers) == 1 else ""


def normalize_contract_ref(contract_ref):
    """Normalize full, relative and dotted contract references."""
    clean_ref = str(contract_ref).strip().strip("`")
    prefix = "core-kernel/runtime/task_contracts/"
    if clean_ref.startswith(prefix):
        clean_ref = clean_ref[len(prefix) :]
    if "/" not in clean_ref and "." in clean_ref and not clean_ref.endswith(".yaml"):
        family, name = clean_ref.split(".", 1)
        clean_ref = f"{family}/{name}.yaml"
    elif not clean_ref.endswith(".yaml"):
        clean_ref += ".yaml"
    return clean_ref


def _contract_path(contract_ref):
    root = get_shiki_root()
    relative = normalize_contract_ref(contract_ref)
    return root / "core-kernel" / "runtime" / "task_contracts" / relative, relative


def load_task_contract(contract_ref):
    """Resolve an alias and return one normalized canonical task contract."""
    requested_path, requested_ref = _contract_path(contract_ref)
    requested = _load_yaml(requested_path.read_text(encoding="utf-8")) or {}
    kind = requested.get("kind")
    if kind == "alias":
        _validate_alias(requested, requested_ref)
        canonical_path, canonical_ref = _contract_path(requested["canonical"])
        canonical = _load_yaml(canonical_path.read_text(encoding="utf-8")) or {}
        if canonical.get("kind") != "canonical":
            raise ValueError(f"{requested_ref} alias must point directly to a canonical contract")
        bindings = requested.get("bindings", {}) or {}
        resolution = "alias"
    elif kind == "canonical":
        canonical = requested
        canonical_path, canonical_ref = requested_path, requested_ref
        bindings = {}
        resolution = "canonical"
    else:
        raise ValueError(f"{requested_ref} has unsupported contract kind: {kind}")

    _validate_canonical(canonical, canonical_ref)
    data = _normalize_contract(canonical)
    data["_path"] = str(canonical_path)
    data["_requested_ref"] = requested_ref
    data["_canonical_ref"] = canonical_ref
    data["_resolution"] = resolution
    data["_bindings"] = bindings
    if bindings:
        data["bindings"] = dict(bindings)
    return data


def _validate_alias(data, contract_ref):
    missing = [field for field in ALIAS_REQUIRED_FIELDS if field not in data]
    if missing:
        raise ValueError(f"{contract_ref} missing alias fields: {', '.join(missing)}")
    extra = sorted(set(data) - ALIAS_ALLOWED_FIELDS)
    if extra:
        raise ValueError(f"{contract_ref} has unsupported alias fields: {', '.join(extra)}")
    bindings = data.get("bindings", {}) or {}
    if not isinstance(bindings, dict):
        raise ValueError(f"{contract_ref} alias bindings must be a mapping")


def _validate_canonical(data, contract_ref):
    missing = [field for field in CANONICAL_REQUIRED_FIELDS if field not in data]
    if missing:
        raise ValueError(f"{contract_ref} missing canonical fields: {', '.join(missing)}")
    extra = sorted(set(data) - CANONICAL_ALLOWED_FIELDS)
    if extra:
        raise ValueError(f"{contract_ref} has unsupported canonical fields: {', '.join(extra)}")
    inputs = data.get("inputs")
    if not isinstance(inputs, list):
        raise ValueError(f"{contract_ref} inputs must be a list")
    for entry in inputs:
        if not isinstance(entry, dict) or set(entry) != {"path", "required"}:
            raise ValueError(f"{contract_ref} input must contain only path and required")
        if not isinstance(entry["path"], str) or not entry["path"].strip():
            raise ValueError(f"{contract_ref} input path must be a non-empty string")
        if not isinstance(entry["required"], bool):
            raise ValueError(f"{contract_ref} input required must be boolean")
    output = data.get("output")
    if output is not None:
        if not isinstance(output, dict) or set(output) != {"path"}:
            raise ValueError(f"{contract_ref} output must contain only path")
        if not isinstance(output["path"], str) or not output["path"].strip():
            raise ValueError(f"{contract_ref} output path must be a non-empty string")


def normalize_artifact_key(value):
    """Normalize matching paths without changing the stored contract shape."""
    clean = str(value).strip().strip("`")
    clean = clean.split("#", 1)[0].strip()
    if clean.startswith("shiki_context/"):
        clean = clean[len("shiki_context/") :]
    return clean


def build_artifact_owner_index(contract_root=None):
    """Index required output patterns to their owner task contracts."""
    root = contract_root or (get_shiki_root() / "core-kernel" / "runtime" / "task_contracts")
    owners = {}
    for path in sorted(root.rglob("*.yaml")):
        raw = _load_yaml(path.read_text(encoding="utf-8")) or {}
        if raw.get("kind", "canonical") != "canonical":
            continue
        data = _normalize_contract(raw)
        output = data.get("output", {})
        if not isinstance(output, dict):
            continue
        key = normalize_artifact_key(output.get("path", ""))
        if not key or key in {"plan output_files", "test evidence", "baseline"}:
            continue
        contract_ref = path.relative_to(root).as_posix()
        owners.setdefault(key, []).append(contract_ref)
    return {key: tuple(values) for key, values in owners.items()}


def recommend_producer(missing_artifact, contract_root=None):
    """Return the task contract(s) that own a missing required artifact."""
    key = normalize_artifact_key(missing_artifact)
    owners = build_artifact_owner_index(contract_root)
    return ProducerRecommendation(key, owners.get(key, ()))


def _normalize_contract(data):
    """Add runtime input lists without changing the Canonical wire shape."""
    if data is None:
        data = {}
    inputs = data.get("inputs", [])
    if not isinstance(inputs, list):
        raise ValueError("task contract inputs must be a list")
    required_inputs = []
    optional_inputs = []
    for raw_input in inputs:
        value = raw_input["path"].strip()
        required = raw_input["required"]
        if required:
            required_inputs.append(value)
        else:
            optional_inputs.append(value)
    data["required_inputs"] = required_inputs
    data["optional_inputs"] = optional_inputs
    return data


def _load_yaml(text):
    """Load YAML text with a dependency-free fallback."""
    try:
        import yaml

        return yaml.safe_load(text)
    except Exception:
        return _load_yaml_fallback(text)


def _load_yaml_fallback(text):
    """Parse the restricted YAML subset used by task contracts."""
    lines = [line.rstrip() for line in text.splitlines()]

    def indent_of(line):
        return len(line) - len(line.lstrip(" "))

    def skip_empty(index):
        while index < len(lines):
            raw = lines[index]
            stripped = raw.strip()
            if stripped and not stripped.startswith("#"):
                break
            index += 1
        return index

    def parse_scalar(value):
        if value in {"null", "Null", "NULL"}:
            return None
        if value in {"true", "True"}:
            return True
        if value in {"false", "False"}:
            return False
        if value.isdigit():
            return int(value)
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            return ast.literal_eval(value)
        return value

    def parse_block(index, indent):
        index = skip_empty(index)
        if index >= len(lines):
            return None, index

        line = lines[index]
        current_indent = indent_of(line)
        if current_indent < indent:
            return None, index

        stripped = line[current_indent:]
        if stripped.startswith("- "):
            values = []
            while True:
                index = skip_empty(index)
                if index >= len(lines):
                    break
                line = lines[index]
                current_indent = indent_of(line)
                if current_indent < indent or current_indent != indent:
                    break
                stripped = line[current_indent:]
                if not stripped.startswith("- "):
                    break
                item = stripped[2:].strip()
                if item:
                    key, separator, raw_value = item.partition(":")
                    if separator:
                        entry = {key.strip(): parse_scalar(raw_value.strip()) if raw_value.strip() else None}
                        continuation, next_index = parse_block(index + 1, indent + 2)
                        if isinstance(continuation, dict):
                            entry.update(continuation)
                            index = next_index
                        else:
                            index += 1
                        values.append(entry)
                        continue
                    values.append(parse_scalar(item))
                    index += 1
                    continue
                nested, index = parse_block(index + 1, indent + 2)
                values.append(nested)
            return values, index

        mapping = {}
        while True:
            index = skip_empty(index)
            if index >= len(lines):
                break
            line = lines[index]
            current_indent = indent_of(line)
            if current_indent < indent or current_indent != indent:
                break
            stripped = line[current_indent:]
            if stripped.startswith("- "):
                break
            key, separator, value = stripped.partition(":")
            if not separator:
                raise ValueError(f"invalid yaml line: {line}")
            key = key.strip()
            value = value.strip()
            if value:
                mapping[key] = parse_scalar(value)
                index += 1
                continue
            child_index = skip_empty(index + 1)
            child_indent = indent + 2
            if child_index < len(lines):
                detected_indent = indent_of(lines[child_index])
                if detected_indent > current_indent:
                    child_indent = detected_indent
                elif lines[child_index].lstrip().startswith("- "):
                    child_indent = current_indent
            nested, index = parse_block(index + 1, child_indent)
            mapping[key] = nested
        return mapping, index

    parsed, _ = parse_block(0, 0)
    if not isinstance(parsed, dict):
        raise ValueError("task contract root must be a mapping")
    return parsed
