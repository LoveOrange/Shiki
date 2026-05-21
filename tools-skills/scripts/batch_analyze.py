#!/usr/bin/env python3
"""Compatibility wrapper for the plan-based Init analyzer."""

import sys

import scan


def main() -> int:
    argv = [sys.argv[0], "--analyze-only", *sys.argv[1:]]
    if "--sync-only" in sys.argv[1:]:
        argv = [sys.argv[0], "--sync-only", *[arg for arg in sys.argv[1:] if arg != "--sync-only"]]
    sys.argv = argv
    return scan.main()


if __name__ == "__main__":
    raise SystemExit(main())
