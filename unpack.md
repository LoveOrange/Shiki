#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Restore files renamed to .md by pack.sh or pack_source.sh.

Usage:
    python unpack.md
"""
import os
import sys


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mapfile = os.path.join(script_dir, "_filemap.md")

    if not os.path.exists(mapfile):
        print("No restore needed: _filemap.md was not found.")
        return

    count = 0
    errors = []

    with open(mapfile, "r") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments.
            if not line or line.startswith("#"):
                continue

            parts = line.split(" -> ", 1)
            if len(parts) != 2:
                continue

            renamed, original = parts[0].strip(), parts[1].strip()
            src = os.path.join(script_dir, renamed)
            dst = os.path.join(script_dir, original)

            if not os.path.exists(src):
                errors.append("  skipped missing file: %s" % renamed)
                continue

            # Ensure the target directory exists.
            dst_dir = os.path.dirname(dst)
            if dst_dir and not os.path.exists(dst_dir):
                os.makedirs(dst_dir)

            os.rename(src, dst)
            count += 1
            print("  restored: %s -> %s" % (renamed, original))

    # Remove the mapping file after a successful pass.
    os.remove(mapfile)

    if errors:
        print("\nWarnings:")
        for e in errors:
            print(e)

    print("\nRestore complete: %d files" % count)


if __name__ == "__main__":
    main()
