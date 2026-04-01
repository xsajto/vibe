#!/usr/bin/env python3
"""Validate SKILL.md frontmatter fields against Claude Code documentation.

Reference: https://code.claude.com/docs/en/skills
"""

import sys
import os
import re
import yaml
from pathlib import Path

VALID_FIELDS = {
    "name",
    "description",
    "argument-hint",
    "disable-model-invocation",
    "user-invocable",
    "allowed-tools",
    "model",
    "effort",
    "context",
    "agent",
    "hooks",
    "paths",
    "shell",
}

VALID_EFFORT_VALUES = {"low", "medium", "high", "max"}
VALID_CONTEXT_VALUES = {"fork"}
VALID_SHELL_VALUES = {"bash", "powershell"}

FIELD_TYPES = {
    "name": str,
    "description": str,
    "argument-hint": str,
    "disable-model-invocation": bool,
    "user-invocable": bool,
    "allowed-tools": list,
    "model": str,
    "effort": str,
    "context": str,
    "agent": str,
    "hooks": dict,
    "paths": list,
    "shell": str,
}


def extract_frontmatter(filepath):
    """Extract YAML frontmatter from a markdown file."""
    with open(filepath, "r") as f:
        content = f.read()

    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None, "No YAML frontmatter found"

    try:
        data = yaml.safe_load(match.group(1))
        return data, None
    except yaml.YAMLError as e:
        return None, f"Invalid YAML: {e}"


def validate_skill(filepath):
    """Validate a single SKILL.md file. Returns list of (level, message) tuples."""
    issues = []
    data, error = extract_frontmatter(filepath)

    if error:
        issues.append(("error", error))
        return issues

    if not isinstance(data, dict):
        issues.append(("error", "Frontmatter is not a YAML mapping"))
        return issues

    # Check for unknown fields
    for key in data:
        if key not in VALID_FIELDS:
            issues.append(("error", f"Unknown field '{key}' — not in Claude Code docs"))

    # Check field types
    for key, value in data.items():
        if key in FIELD_TYPES and value is not None:
            expected = FIELD_TYPES[key]
            if not isinstance(value, expected):
                issues.append((
                    "error",
                    f"Field '{key}' should be {expected.__name__}, got {type(value).__name__}"
                ))

    # Validate specific field values
    if "effort" in data and data["effort"] not in VALID_EFFORT_VALUES:
        issues.append((
            "error",
            f"Field 'effort' must be one of {VALID_EFFORT_VALUES}, got '{data['effort']}'"
        ))

    if "context" in data and data["context"] not in VALID_CONTEXT_VALUES:
        issues.append((
            "error",
            f"Field 'context' must be one of {VALID_CONTEXT_VALUES}, got '{data['context']}'"
        ))

    if "shell" in data and data["shell"] not in VALID_SHELL_VALUES:
        issues.append((
            "error",
            f"Field 'shell' must be one of {VALID_SHELL_VALUES}, got '{data['shell']}'"
        ))

    # Check name format (lowercase, hyphens, max 64 chars)
    if "name" in data and isinstance(data["name"], str):
        name = data["name"]
        if len(name) > 64:
            issues.append(("error", f"Field 'name' exceeds 64 characters ({len(name)})"))
        if not re.match(r"^[a-z0-9-]+$", name):
            issues.append(("warn", f"Field 'name' should be lowercase with hyphens only, got '{name}'"))

    # Check allowed-tools is a list, not comma-separated string
    if "allowed-tools" in data and isinstance(data["allowed-tools"], str):
        issues.append((
            "error",
            "Field 'allowed-tools' must be a YAML list, not a comma-separated string"
        ))

    # Warnings for recommended fields
    if "description" not in data or not data.get("description"):
        issues.append(("warn", "Missing 'description' — recommended for auto-invocation"))

    # Check agent requires context: fork
    if "agent" in data and data.get("context") != "fork":
        issues.append(("warn", "Field 'agent' is set but 'context' is not 'fork'"))

    return issues


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    skill_files = sorted(root.rglob("SKILL.md"))

    if not skill_files:
        print("No SKILL.md files found")
        sys.exit(1)

    total_errors = 0
    total_warnings = 0

    for filepath in skill_files:
        rel_path = filepath.relative_to(root)
        issues = validate_skill(filepath)

        errors = [msg for level, msg in issues if level == "error"]
        warnings = [msg for level, msg in issues if level == "warn"]
        total_errors += len(errors)
        total_warnings += len(warnings)

        if errors or warnings:
            print(f"\n{'✗' if errors else '⚠'} {rel_path}")
            for msg in errors:
                print(f"  ✗ {msg}")
            for msg in warnings:
                print(f"  ⚠ {msg}")
        else:
            print(f"✔ {rel_path}")

    print(f"\n{'─' * 50}")
    print(f"Files: {len(skill_files)}  Errors: {total_errors}  Warnings: {total_warnings}")

    if total_errors > 0:
        print("✗ Validation failed")
        sys.exit(1)
    else:
        print("✔ Validation passed" + (" with warnings" if total_warnings else ""))
        sys.exit(0)


if __name__ == "__main__":
    main()
