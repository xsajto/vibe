# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repository is a **Claude Code plugin marketplace** that distributes plugins with skills, agents, hooks, and MCP servers.

## Documentation

Before creating or updating plugins, skills, or the marketplace definition, you MUST read the official documentation:

- **Plugins**: https://code.claude.com/docs/en/plugins
- **Plugin Marketplaces**: https://code.claude.com/docs/en/plugin-marketplaces
- **Skills**: https://code.claude.com/docs/en/skills
- **Plugins Reference**: https://code.claude.com/docs/en/plugins-reference

## Structure

This is a marketplace repository with the following layout:

```
.claude-plugin/
  marketplace.json          # Marketplace catalog listing all plugins
plugins/
  <plugin-name>/
    .claude-plugin/
      plugin.json           # Plugin manifest (name, description, version)
    skills/
      <skill-name>/
        SKILL.md            # Skill definition with frontmatter
    .mcp.json               # MCP server configurations (optional)
    agents/                 # Agent definitions (optional)
    hooks/                  # Hook configurations (optional)
templates/
  skill/
    SKILL.md                # Skill template for creating new skills
```

## Key Rules

- Each plugin is a self-contained directory under `plugins/` with its own `.claude-plugin/plugin.json`
- Skills live in `skills/<name>/SKILL.md` inside each plugin directory
- MCP servers are configured in `.mcp.json` at the plugin root
- The marketplace catalog at `.claude-plugin/marketplace.json` references all plugins
- Plugin names must be kebab-case
- Skills are namespaced: `/plugin-name:skill-name`
- Use `"source": "./plugins/<name>"` for plugins within this repo
- Use `"strict": false` when the marketplace entry defines everything
