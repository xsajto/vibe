---
name: marketplace-builder
description: >
  Create and manage Claude Code plugin marketplaces with plugins containing skills, hooks, agents, and MCP servers.
  Use when the user wants to: create a plugin marketplace, add plugins to a marketplace, scaffold a new plugin,
  write marketplace.json or plugin.json, or build any Claude Code extension package.
---

# Claude Code Marketplace Builder

## Workflow

### 1. Create Directory Structure

```
my-marketplace/
  .claude-plugin/
    marketplace.json        # Marketplace catalog (required)
  plugins/
    <plugin-name>/
      .claude-plugin/
        plugin.json         # Plugin manifest
      skills/               # Skills: <name>/SKILL.md
      agents/               # Agent .md files
      hooks/                # hooks.json
      .mcp.json             # MCP server configs
```

### 2. Write marketplace.json

Place at `.claude-plugin/marketplace.json`. Full schema: [marketplace-schema.md](references/marketplace-schema.md).

```json
{
  "name": "my-marketplace",
  "owner": { "name": "Your Name" },
  "plugins": [
    {
      "name": "my-plugin",
      "source": "./plugins/my-plugin",
      "description": "What this plugin does"
    }
  ]
}
```

Rules:
- `name` must be kebab-case
- `"source": "./plugins/<name>"` for plugins within the repo
- Paths resolve relative to marketplace root (directory containing `.claude-plugin/`), NOT relative to `marketplace.json`
- Do NOT use `../` in paths

### 3. Create Plugins

Each plugin needs `.claude-plugin/plugin.json`. Full schema: [plugin-schema.md](references/plugin-schema.md).

```json
{
  "name": "my-plugin",
  "description": "Brief description",
  "version": "1.0.0"
}
```

Rules:
- `name` must be kebab-case, becomes skill namespace (`/my-plugin:skill-name`)
- Component directories (`skills/`, `agents/`, `hooks/`) go at plugin root, NOT inside `.claude-plugin/`
- Use `${CLAUDE_PLUGIN_ROOT}` in hook commands and MCP configs to reference plugin files

### 4. Add Skills

Create `skills/<skill-name>/SKILL.md`:

```yaml
---
name: my-skill
description: What it does and when to use it
---

Instructions for Claude when this skill is active.
```

Use `$ARGUMENTS` for user input, `$ARGUMENTS[N]` or `$N` for positional args.

### 5. Add Other Components

**Agents** (`agents/*.md`):
```yaml
---
name: my-agent
description: What this agent specializes in
model: sonnet
maxTurns: 20
---
System prompt for the agent.
```

**Hooks** (`hooks/hooks.json`):
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{ "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/scripts/lint.sh" }]
    }]
  }
}
```

**MCP Servers** (`.mcp.json`):
```json
{
  "mcpServers": {
    "my-server": {
      "command": "${CLAUDE_PLUGIN_ROOT}/server.js",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"]
    }
  }
}
```

### 6. Plugin Sources (external plugins)

For plugins NOT in the same repo. See [marketplace-schema.md](references/marketplace-schema.md#plugin-sources).

```json
{ "source": { "source": "github", "repo": "owner/repo", "ref": "v2.0" } }
{ "source": { "source": "npm", "package": "@org/plugin", "version": "^2.0" } }
{ "source": { "source": "url", "url": "https://gitlab.com/team/plugin.git" } }
{ "source": { "source": "git-subdir", "url": "https://github.com/org/monorepo.git", "path": "tools/plugin" } }
```

### 7. Validate and Test

```bash
claude plugin validate .
/plugin marketplace add ./path/to/marketplace
/plugin install my-plugin@marketplace-name
```
