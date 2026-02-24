# fixpoint-scraper

A Claude Code plugin that provides an AI-powered web scraping skill. It navigates a website using the Playwright MCP server, records structured interaction traces, then generates a standalone deterministic Playwright scraper in TypeScript.

## Usage

```
/fixpoint-scraper:scrape <url> <query>
```

For example:

```
/fixpoint-scraper:scrape https://example.com/products Extract all product names and prices
```

## How it works

The scraper operates in two phases:

**Phase 1 — AI-Powered Navigation:** Claude navigates the target site using the Playwright MCP browser, interacting with elements to fulfill your query. It records a structured trace of every action (clicks, fills, scrolls, etc.) along with a narrative describing the scraping strategy.

**Phase 2 — Deterministic Scraper Generation:** Using the recorded traces and narrative, Claude generates a standalone TypeScript Playwright script that deterministically reproduces the scraping flow. The generated scraper runs without any AI/LLM dependencies — just Playwright.

## Prerequisites

This plugin requires the [Playwright MCP server](https://github.com/anthropics/mcp-playwright) to be configured in your Claude Code environment. The Playwright MCP server provides browser automation capabilities that the scraping skill depends on.

## Installation

Add this plugin to your Claude Code configuration:

```json
{
  "plugins": ["github:gofixpoint/agent-plugins"]
}
```

## License

Apache-2.0
