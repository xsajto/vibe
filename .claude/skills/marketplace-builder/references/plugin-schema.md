# Plugin Schema Reference

## plugin.json (`.claude-plugin/plugin.json`)

Optional. If omitted, Claude Code auto-discovers components in default locations.

### Required Fields

| Field  | Type   | Description                                            |
|--------|--------|--------------------------------------------------------|
| `name` | string | Kebab-case identifier, becomes skill namespace (`/name:skill`) |

### Metadata Fields

| Field         | Type   | Description                |
|---------------|--------|----------------------------|
| `version`     | string | Semver (`MAJOR.MINOR.PATCH`) |
| `description` | string | Brief plugin purpose       |
| `author`      | object | `name`, `email`, `url`     |
| `homepage`    | string | Documentation URL          |
| `repository`  | string | Source code URL             |
| `license`     | string | SPDX identifier            |
| `keywords`    | array  | Discovery tags             |

### Component Path Fields

| Field          | Type                  | Default Location   |
|----------------|-----------------------|--------------------|
| `commands`     | string\|array         | `commands/`        |
| `agents`       | string\|array         | `agents/`          |
| `skills`       | string\|array         | `skills/`          |
| `hooks`        | string\|array\|object | `hooks/hooks.json` |
| `mcpServers`   | string\|array\|object | `.mcp.json`        |
| `lspServers`   | string\|array\|object | `.lsp.json`        |
| `outputStyles` | string\|array         | `output-styles/`   |

Custom paths replace defaults. To keep defaults AND add more: `"commands": ["./commands/", "./extras/cmd.md"]`

## Directory Structure

```
plugin-name/
  .claude-plugin/
    plugin.json              # Manifest (optional)
  skills/                    # Skills: <name>/SKILL.md
  agents/                    # Agent .md files
  hooks/
    hooks.json               # Hook configuration
  .mcp.json                  # MCP server configs
  scripts/                   # Hook and utility scripts
```

**Critical**: Component directories go at plugin root, NOT inside `.claude-plugin/`.

## Environment Variables

| Variable                 | Description                                       |
|--------------------------|---------------------------------------------------|
| `${CLAUDE_PLUGIN_ROOT}`  | Plugin install directory (changes on update)      |
| `${CLAUDE_PLUGIN_DATA}`  | Persistent data directory (survives updates)      |

## SKILL.md Frontmatter

| Field                      | Type         | Description                               |
|----------------------------|--------------|-------------------------------------------|
| `name`                     | string       | Slash-command name (kebab-case, max 64)   |
| `description`              | string       | What it does and when to use it           |
| `argument-hint`            | string       | Autocomplete hint                         |
| `disable-model-invocation` | boolean      | Manual `/name` only                       |
| `user-invocable`           | boolean      | Show in `/` menu (default: true)          |
| `allowed-tools`            | string       | Tools allowed without permission          |
| `model`                    | string       | Model override                            |
| `effort`                   | string       | `low`, `medium`, `high`, `max`            |
| `context`                  | string       | `fork` for isolated subagent              |
| `agent`                    | string       | Subagent type when `context: fork`        |
| `paths`                    | string\|list | Glob patterns for auto-activation         |

## Agent Frontmatter

| Field             | Type    | Description                    |
|-------------------|---------|--------------------------------|
| `name`            | string  | Agent identifier               |
| `description`     | string  | When Claude should invoke it   |
| `model`           | string  | Model to use                   |
| `maxTurns`        | number  | Maximum turns                  |
| `tools`           | string  | Allowed tools                  |
| `disallowedTools` | string  | Denied tools                   |
| `isolation`       | string  | Only `"worktree"` supported   |

NOT supported in plugin agents: `hooks`, `mcpServers`, `permissionMode`.

## Hook Events

`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `Stop`, `Notification`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `FileChanged`, `CwdChanged`, `SessionEnd`.

Hook types: `command`, `http`, `prompt`, `agent`.
