"""Machine-readable task contract loader.

Task contracts are stored as YAML for human readability. Runtime loading prefers
PyYAML when available and falls back to a tiny parser that supports the limited
subset used by Shiki task contracts.
"""

import ast

from .paths import get_shiki_root


REQUIRED_FIELDS = (
    "id",
    "stage",
    "kind",
    "goal",
    "inputs",
    "references",
    "checks",
    "done_condition",
    "workflow_ref",
)

DEFAULT_FIELDS = {
    "artifact": {
        "path": "",
        "mode": "update",
        "template": "",
    },
    "evidence_rules": [],
    "retry_policy": {
        "max_attempts": 1,
    },
}


def load_task_contract(contract_ref):
    """Load a task contract from core-kernel/runtime/task_contracts/."""
    root = get_shiki_root()
    path = root / contract_ref
    data = _load_yaml(path.read_text(encoding="utf-8"))
    data = _normalize_contract(data)
    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        raise ValueError(f"{contract_ref} missing task contract fields: {', '.join(missing)}")
    data["_path"] = str(path)
    return data


def _normalize_contract(data):
    """Backfill optional runtime fields and legacy aliases."""
    if data is None:
        data = {}
    for key, value in DEFAULT_FIELDS.items():
        data.setdefault(key, value)

    if "tech_contract" not in data:
        packs = data.get("tech_contracts", "tech_stacks")
        if isinstance(packs, list):
            data["tech_contract"] = ",".join(str(item) for item in packs)
        else:
            data["tech_contract"] = packs
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
            nested, index = parse_block(index + 1, indent + 2)
            mapping[key] = nested
        return mapping, index

    parsed, _ = parse_block(0, 0)
    if not isinstance(parsed, dict):
        raise ValueError("task contract root must be a mapping")
    return parsed
