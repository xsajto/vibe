# vibe

A Claude Code plugin marketplace for DevOps, monitoring, and research workflows.

## Installation

Add this marketplace and install plugins:

```bash
/plugin marketplace add xsajto/vibe
/plugin install prometheus-skill@xsajto-vibe-skills
/plugin install grafana-skill@xsajto-vibe-skills
/plugin install loki-skill@xsajto-vibe-skills
/plugin install researching-web-skill@xsajto-vibe-skills
/plugin install deepwiki@xsajto-vibe-skills
```

## Plugins

| Plugin | Description | Source |
|--------|-------------|--------|
| [prometheus-skill](plugins/prometheus-skill/) | Query Prometheus HTTP API, execute PromQL, manage targets/alerts/rules | [julianobarbosa/claude-code-skills](https://github.com/julianobarbosa/claude-code-skills/tree/main/skills/prometheus-skill) |
| [grafana-skill](plugins/grafana-skill/) | Interact with Grafana API for dashboards, datasources, alerting, and annotations | [julianobarbosa/claude-code-skills](https://github.com/julianobarbosa/claude-code-skills/tree/main/skills/grafana-skill) |
| [loki-skill](plugins/loki-skill/) | Query Loki log aggregation system via LogQL | [julianobarbosa/claude-code-skills](https://github.com/julianobarbosa/claude-code-skills/tree/main/skills/loki-skill) |
| [researching-web-skill](plugins/researching-web-skill/) | Web research using Perplexity AI for current information and best practices | [julianobarbosa/claude-code-skills](https://github.com/julianobarbosa/claude-code-skills/tree/main/skills/researching-web-skill) |
| [deepwiki](plugins/deepwiki/) | AI-powered docs for any public GitHub repo — browse structure, read docs, ask questions | [DeepWiki MCP](https://docs.devin.ai/work-with-devin/deepwiki-mcp) |

## Creating New Plugins

Use the template at [`templates/skill/SKILL.md`](templates/skill/SKILL.md) as a starting point for skills. See the [Claude Code plugins documentation](https://code.claude.com/docs/en/plugins) for the full reference.

Each plugin follows this structure:

```
plugins/<plugin-name>/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest
├── skills/
│   └── <skill-name>/
│       └── SKILL.md          # Skill definition
├── .mcp.json                 # MCP server configurations (optional)
├── scripts/                  # Helper scripts (optional)
└── references/               # Reference docs (optional)
```

## Sources

This marketplace aggregates plugins from:

- **[julianobarbosa/claude-code-skills](https://github.com/julianobarbosa/claude-code-skills)** — Prometheus, Grafana, Loki, and web research skills
- **[DeepWiki MCP](https://docs.devin.ai/work-with-devin/deepwiki-mcp)** — AI-powered documentation for public GitHub repositories
