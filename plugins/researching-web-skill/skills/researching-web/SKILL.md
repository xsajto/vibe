---
name: researching-web
description: Search the web using open-webSearch. Use when needing to search, look up, research, find current information, best practices, compare technologies, or answer factual questions.
disable-model-invocation: true
---

# Web Research with open-webSearch

You have access to open-webSearch MCP tools for searching the web and fetching content.
No API key required — uses free search engines (DuckDuckGo, Bing, Brave, StartPage).

## Available Tools

| Tool | Purpose |
|------|---------|
| `mcp__web-search__search` | Search the web with configurable engines and result limits |
| `mcp__web-search__fetchWebContent` | Fetch and convert any URL to readable markdown |
| `mcp__web-search__fetchGithubReadme` | Fetch a GitHub repository README |

## Usage Patterns

### Web Search

Parameters:
- `query` (required): The search query string
- `limit` (optional): Number of results to return (default: 10)
- `engines` (optional): Array of engines — `bing`, `duckduckgo`, `brave`, `startpage`

### Fetch Page Content

Use `fetchWebContent` to retrieve the full content of a URL as markdown.
Useful for reading documentation, blog posts, or articles found via search.

### Fetch GitHub READMEs

Use `fetchGithubReadme` for quick access to repository documentation.

## Tips

- Start with `search`, then use `fetchWebContent` to dive into specific results
- Use multiple engines for better coverage on important queries
- Be specific: "Go error handling best practices 2025"
- Include context: "Redis vs Memcached for session storage"
- Prefer `fetchGithubReadme` over `fetchWebContent` for GitHub repos
