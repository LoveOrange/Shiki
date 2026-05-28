"""Filesystem helpers for Shiki runtime scripts."""

from pathlib import Path


def get_shiki_root():
    """Locate the Shiki framework root (parent of scripts/)."""
    return Path(__file__).resolve().parents[2]


def get_project_root():
    """Get the project root that contains shiki/ and shiki_context/."""
    return get_shiki_root().parent


def get_context_dir():
    """Get the shiki_context directory path."""
    return get_project_root() / "shiki_context"


def get_feature_dir(feature_id):
    """Get a feature directory under shiki_context/features/."""
    return get_context_dir() / "features" / feature_id


def resolve_code_contract(feature_dir):
    """Return the optional implementation slice path."""
    return feature_dir / "code_contract.md"
