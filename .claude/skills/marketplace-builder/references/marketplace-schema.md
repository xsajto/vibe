# Marketplace Schema Reference

## marketplace.json Required Fields

| Field     | Type   | Description                                    |
|-----------|--------|------------------------------------------------|
| `name`    | string | Kebab-case identifier. Users see it in install commands. |
| `owner`   | object | `name` (required), `email` (optional)          |
| `plugins` | array  | List of plugin entries                         |

**Reserved names**: `claude-code-marketplace`, `claude-code-plugins`, `claude-plugins-official`, `anthropic-marketplace`, `anthropic-plugins`, `agent-skills`, `knowledge-work-plugins`, `life-sciences`.

## Optional Metadata

| Field                  | Type   | Description                                    |
|------------------------|--------|------------------------------------------------|
| `metadata.description` | string | Brief marketplace description                  |
| `metadata.version`     | string | Marketplace version                            |
| `metadata.pluginRoot`  | string | Base directory prepended to relative plugin source paths |

## Plugin Entry Fields

### Required

| Field    | Type           | Description                                    |
|----------|----------------|------------------------------------------------|
| `name`   | string         | Kebab-case plugin identifier                   |
| `source` | string\|object | Where to fetch the plugin                      |

### Optional

| Field         | Type           | Description                                 |
|---------------|----------------|---------------------------------------------|
| `description` | string         | Brief plugin description                    |
| `version`     | string         | Plugin version (plugin.json wins if both set) |
| `author`      | object         | `name` (required), `email` (optional)       |
| `homepage`    | string         | Documentation URL                           |
| `repository`  | string         | Source code URL                              |
| `license`     | string         | SPDX identifier                             |
| `keywords`    | array          | Discovery tags                              |
| `category`    | string         | Organization category                       |
| `tags`        | array          | Searchability tags                          |
| `strict`      | boolean        | Component authority (default: true)         |
| `commands`    | string\|array  | Custom command paths                        |
| `agents`      | string\|array  | Custom agent paths                          |
| `hooks`       | string\|object | Hook config or path                         |
| `mcpServers`  | string\|object | MCP config or path                          |
| `lspServers`  | string\|object | LSP config or path                          |

### Strict Mode

| Value            | Behavior                                                          |
|------------------|-------------------------------------------------------------------|
| `true` (default) | `plugin.json` is authority. Marketplace entry supplements/merges. |
| `false`          | Marketplace entry is the entire definition. Plugin must NOT declare components in `plugin.json`. |

## Plugin Sources

### Relative Path (same repo)
```json
{ "name": "my-plugin", "source": "./plugins/my-plugin" }
```
Must start with `./`. Only works with git-based marketplaces.

### GitHub
```json
{
  "source": { "source": "github", "repo": "owner/repo", "ref": "v2.0.0", "sha": "a1b2c3..." }
}
```

### Git URL
```json
{
  "source": { "source": "url", "url": "https://gitlab.com/team/plugin.git", "ref": "main" }
}
```

### Git Subdirectory (monorepos)
```json
{
  "source": { "source": "git-subdir", "url": "https://github.com/org/monorepo.git", "path": "tools/plugin" }
}
```

### npm
```json
{
  "source": { "source": "npm", "package": "@acme/plugin", "version": "^2.0.0", "registry": "https://npm.example.com" }
}
```
