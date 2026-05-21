#!/usr/bin/env python3
"""Compatibility wrapper for the bundled spec-to-html publisher."""

import runpy
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "tools-skills" / "skills" / "spec-to-html" / "scripts" / "publish_docs.py"


if __name__ == "__main__":
    runpy.run_path(str(SCRIPT), run_name="__main__")
