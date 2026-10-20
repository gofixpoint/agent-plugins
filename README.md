# agent-plugins

A grab bag of agent skills the [Amika](https://github.com/gofixpoint/amika) team has found useful. They aren't a coherent product, just tools we built for our own work and figured others might want too. Each skill lives in its own folder under [`skills/`](skills/), and they all ship together as one Claude Code plugin.

Made with love by [Amika](https://github.com/gofixpoint/amika). Join us on [Discord](https://discord.gg/xDXk4KjGWg) to chat about software factories and agentic software.

## Installation

Add this plugin to your Claude Code configuration:

```json
{
  "plugins": ["github:gofixpoint/agent-plugins"]
}
```

Skills are invoked as `/amika-scraper:<skill>`, using the plugin name from [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json).

## Skills

| Skill | What it does | Requires |
| --- | --- | --- |
| [`scrape`](skills/scrape/SKILL.md) | Navigates a site with Playwright, records the interactions, then generates a standalone deterministic Playwright scraper in TypeScript. | [Playwright MCP server](https://github.com/anthropics/mcp-playwright) |

### scrape

```
/amika-scraper:scrape <url> <query>
```

For example:

```
/amika-scraper:scrape https://example.com/products Extract all product names and prices
```

The scraper works in two phases:

1. **AI-powered navigation.** Claude drives the target site through the Playwright MCP browser to fulfill your query, recording a structured trace of every action (clicks, fills, scrolls, etc.) plus a narrative of the scraping strategy.
2. **Deterministic scraper generation.** From the traces and narrative, Claude generates a standalone TypeScript Playwright script that reproduces the flow. The generated scraper has no AI/LLM dependencies, just Playwright.

## Adding a skill

1. Create `skills/<name>/SKILL.md` with `name` and `description` frontmatter, plus any supporting files the skill needs in the same folder.
2. Add a row to the [Skills](#skills) table above, and a short usage section if the skill takes arguments or has prerequisites.

## License

MIT
