---
# Required: lowercase, hyphens only, max 64 chars. Becomes the /slash-command name.
name: my-skill-name

# Recommended: helps Claude decide when to auto-invoke this skill.
description: >
  Brief description of what this skill does and when to use it.
  Example: "Query monitoring APIs when the user needs metrics data."

# Optional: hint shown in the slash command menu for expected arguments.
# argument-hint: "<query>"

# Optional: set true to prevent Claude from auto-invoking (manual /command only).
# disable-model-invocation: false

# Optional: set false to hide from the / menu (background knowledge only).
# user-invocable: true

# Optional: tools Claude can use without asking permission when this skill is active.
# allowed-tools:
#   - Read
#   - Grep
#   - Glob
#   - Bash

# Optional: model override when this skill is active.
# model: sonnet

# Optional: effort level (low/medium/high/max).
# effort: high

# Optional: set to "fork" to run in an isolated subagent context.
# context: fork
# agent: general-purpose

# Optional: glob patterns limiting when this skill auto-activates.
# paths:
#   - "src/**/*.ts"
---

# Skill Name

Brief overview of what this skill does.

## Quick Reference

Key commands, API calls, or patterns for quick access.

```bash
# Example command
example-command --flag value
```

## Usage

Describe when and how to use this skill. Include common scenarios.

## Reference

Detailed documentation, API endpoints, configuration options, etc.

## Scripts

If the skill includes helper scripts, document them here:

```bash
# Run the helper script
python scripts/my_script.py <args>
```

## Detailed Reference

Link to additional reference files if needed:
- [API Reference](references/api_reference.md)
- [Examples](references/examples.md)
