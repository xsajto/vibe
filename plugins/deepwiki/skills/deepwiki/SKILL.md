---
name: deepwiki
description: >
  Look up documentation for any public GitHub repository using DeepWiki.
  Use when you need to understand how a library, framework, or tool works,
  explore its API, or answer questions about its codebase.
allowed-tools:
  - mcp__deepwiki__read_wiki_structure
  - mcp__deepwiki__read_wiki_contents
  - mcp__deepwiki__ask_question
---

# DeepWiki — Repository Documentation Lookup

You have access to DeepWiki MCP tools for querying AI-generated documentation about any public GitHub repository.

## Available Tools

| Tool | Purpose |
|------|---------|
| `mcp__deepwiki__read_wiki_structure` | Get the list of documentation topics for a repository |
| `mcp__deepwiki__read_wiki_contents` | Read full documentation content for a repository |
| `mcp__deepwiki__ask_question` | Ask a specific question about a repository and get an AI-powered answer |

## Usage Patterns

### Explore a repository's documentation

1. First call `read_wiki_structure` with the repo (e.g. `owner/repo`) to see available topics
2. Then call `read_wiki_contents` to read specific sections you need

### Answer a specific question

Use `ask_question` directly when you have a focused question about a repository. This is the fastest path — no need to browse structure first.

### Examples

```
# What authentication methods does supabase-js support?
ask_question("supabase/supabase-js", "What authentication methods are available?")

# How does the Next.js router work?
ask_question("vercel/next.js", "How does the app router handle nested layouts?")

# Explore a library you're unfamiliar with
read_wiki_structure("pallets/flask")
read_wiki_contents("pallets/flask", "routing")
```

## Guidelines

- Always use the `owner/repo` format (e.g. `facebook/react`, not just `react`)
- Works only with **public** GitHub repositories
- Start with `ask_question` for specific queries — it's faster than browsing
- Use `read_wiki_structure` first when you need a broad overview of what's documented
- DeepWiki generates documentation from the repository source code, so it reflects the current state of the codebase
