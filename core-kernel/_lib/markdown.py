"""Markdown parsing helpers for lightweight runtime validation."""

import re


def read_text(path):
    """Read a UTF-8 text file."""
    return path.read_text(encoding="utf-8")


def metadata_value(text, key):
    """Extract a simple markdown metadata value from '- **Key**: value'."""
    pattern = r"^\s*-\s+\*\*" + re.escape(key) + r"\*\*:\s*(.*?)\s*$"
    match = re.search(pattern, text, re.M)
    if not match:
        return ""
    return match.group(1).strip()


def has_section(text, section_name):
    """Check whether a markdown document contains a section by name."""
    pattern = r"^##\s+.*\b" + re.escape(section_name) + r"\b"
    return re.search(pattern, text, re.M) is not None


def require_sections(text, sections):
    """Return a list of missing section names."""
    return [name for name in sections if not has_section(text, name)]


def extract_section(text, heading_needle):
    """Extract a markdown section block by heading substring."""
    lines = text.splitlines()
    start = None
    level = None

    for index, line in enumerate(lines):
        match = re.match(r"^(#+)\s+(.*)$", line)
        if match and heading_needle in match.group(2):
            start = index + 1
            level = len(match.group(1))
            break

    if start is None:
        return ""

    end = len(lines)
    for index in range(start, len(lines)):
        match = re.match(r"^(#+)\s+", lines[index])
        if match and len(match.group(1)) <= level:
            end = index
            break

    return "\n".join(lines[start:end]).strip()


def parse_table(section_text):
    """Parse the first markdown table found in a section."""
    lines = [line.rstrip() for line in section_text.splitlines()]
    table_start = None

    for index in range(len(lines) - 1):
        if lines[index].strip().startswith("|") and lines[index + 1].strip().startswith("|"):
            table_start = index
            break

    if table_start is None:
        return []

    table_lines = []
    for line in lines[table_start:]:
        if not line.strip():
            break
        if not line.strip().startswith("|"):
            break
        table_lines.append(line.strip())

    if len(table_lines) < 2:
        return []

    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < len(headers):
            cells.extend([""] * (len(headers) - len(cells)))
        row = {}
        for index, header in enumerate(headers):
            row[header] = cells[index]
        rows.append(row)
    return rows

