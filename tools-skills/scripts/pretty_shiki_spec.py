#!/usr/bin/env python3
"""Compatibility wrapper for the bundled pretty-shiki-spec publisher."""

import runpy
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "pretty-shiki-spec"
    / "scripts"
    / "publish_pretty_spec.py"
)


if __name__ == "__main__":
    runpy.run_path(str(SCRIPT), run_name="__main__")
