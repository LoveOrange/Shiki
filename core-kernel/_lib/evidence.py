"""Evidence extraction helpers used by verifier and orchestration logic."""

from .markdown import metadata_value, read_text


def code_contract_valid(feature_dir):
    """Check if optional code_contract.md Code Contract has a concrete version."""
    cp_path = feature_dir / "code_contract.md"
    if not cp_path.exists():
        return False, "code_contract.md missing"
    text = read_text(cp_path)
    version = metadata_value(text, "Contract Version")
    if not version or version in {"[TBD]", "N/A"}:
        return False, "Contract Version not set"
    return True, None


def code_contract_confirmed(feature_dir):
    """Check if all confirmation checkboxes in the optional Code Contract are checked."""
    cp_path = feature_dir / "code_contract.md"
    if not cp_path.exists():
        return False
    text = read_text(cp_path)
    # Count unchecked boxes in confirmation columns
    return "[ ]" not in text
