---
name: scrape
description: >
  AI-powered web scraper that navigates a site with Playwright MCP, records
  interaction traces, then generates a standalone deterministic Playwright
  scraper in TypeScript. Use when the user wants to scrape a website, build
  a scraper, or extract data from a web page.
argument-hint: <url> <query>
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, mcp__plugin_playwright_playwright__browser_navigate, mcp__plugin_playwright_playwright__browser_snapshot, mcp__plugin_playwright_playwright__browser_click, mcp__plugin_playwright_playwright__browser_fill_form, mcp__plugin_playwright_playwright__browser_hover, mcp__plugin_playwright_playwright__browser_press_key, mcp__plugin_playwright_playwright__browser_select_option, mcp__plugin_playwright_playwright__browser_evaluate, mcp__plugin_playwright_playwright__browser_network_requests, mcp__plugin_playwright_playwright__browser_take_screenshot, mcp__plugin_playwright_playwright__browser_navigate_back, mcp__plugin_playwright_playwright__browser_tabs, mcp__plugin_playwright_playwright__browser_drag, mcp__plugin_playwright_playwright__browser_type, mcp__plugin_playwright_playwright__browser_wait_for, mcp__plugin_playwright_playwright__browser_close, mcp__plugin_playwright_playwright__browser_console_messages, mcp__plugin_playwright_playwright__browser_resize, mcp__plugin_playwright_playwright__browser_run_code, mcp__plugin_playwright_playwright__browser_file_upload
---

# Autogen Scraper

You are an intelligent web scraping agent. You will navigate a website using
the Playwright MCP server, record structured traces of your interactions, and
then generate a standalone deterministic Playwright scraper in TypeScript.

**Input:** `$0` is the URL. Everything after the URL is the query: `$ARGUMENTS`.

## Phase 1: AI-Powered Navigation

### Setup

1. **Parse arguments**: Extract the URL from `$0`. The query is everything
   after the URL in `$ARGUMENTS`. If the URL or query is missing, ask the user.

2. **Generate slug**: Create a slug from the URL by removing the protocol,
   replacing non-path-safe characters with hyphens, and appending a timestamp
   (e.g., `example-com-products-20250115T103000`).

3. **Create scratch directory**: `scratch/{slug}/` and the
   `network-requests/` subdirectory within it.

4. **Write metadata.json**: Save URL, query, timestamp, and output format
   (inferred from the query) to `scratch/{slug}/metadata.json`.
   Leave `scraperName` as `null` for now.

### Network Request Capture

Use `browser_network_requests` with the `filename` parameter to save network
traffic to `scratch/{slug}/network-requests/`. This avoids
flooding your context with request bodies. You may inspect these files later
during Phase 2 to decide whether the scraper can use direct HTTP requests. You
can also even inspect these network requests during phase 1 and use that to
determine if you can speed up phase run scraping by making network requests.


### Navigate and Record Traces

Navigate to the URL and interact with the site to fulfill the query. For every
interaction, record a trace entry in `scratch/{slug}/trace.jsonl`.

Each trace line is JSON with these fields:
- **`action`**: The Playwright action (`click`, `fill`, `navigate`, `scroll`,
  `wait`, `select`, `hover`, etc.)
- **`handle`**: How to find the target element (omit for non-element actions):
  - `type`: one of `accessibility`, `id`, `label`, `xpath`, `text`, `llm`
  - `value`: the selector value (or a natural language prompt for `llm` type)
- **`reason`**: Plain language explanation of why you performed this action
- Additional fields as needed (`url` for navigate, `text` for fill, etc.)

**Handle priority** (use the highest available):
1. Accessibility tree target
2. Element `id`
3. Label
4. XPath (only if stable across page loads)
5. Meaningful identifying text
6. LLM-powered handle (last resort only)

**Short-circuiting loops**: If you find yourself repeating the same interaction
pattern in a loop (e.g., clicking "next page" and extracting rows, scrolling and
collecting items), you can short-circuit after a few iterations. The goal in
Phase 1 is to understand the pattern, not to exhaustively process every
iteration. Record enough iterations to capture the loop structure, any variation
between iterations, and the termination condition.

### Write Narrative

Write `scratch/{slug}/narrative.md` describing:
- Your overall scraping strategy
- Any loops, pagination, or multi-step flows
- Why you chose certain approaches
- Difficulties encountered and how you resolved them

This narrative will be given to the agent that writes the Playwright script.

### Restarting

If you get off track or into a weird loop, it is fine to reload the page and
try a different scraping plan.

### Transition to Phase 2

After completing Phase 1:

1. Propose a scraper name (kebab-case, descriptive of what it scrapes).
2. Update `metadata.json` with the proposed `scraperName`.
3. Present the user with:
   - The proposed scraper name
   - A summary of what you did (actions taken, data found)
   - The full paths of all Phase 1 artifact files you wrote:
     - `scratch/{slug}/metadata.json`
     - `scratch/{slug}/trace.jsonl`
     - `scratch/{slug}/narrative.md`
     - `scratch/{slug}/network-requests/` (and list files within)
4. **Ask the user to confirm** before proceeding to Phase 2.

Once the user confirms:

5. Create `{scraper-name}/traces/{slug}/`.
6. Move all files from `scratch/{slug}/` into
   `{scraper-name}/traces/{slug}/` (including
   `metadata.json`, `trace.jsonl`, `narrative.md`, and `network-requests/`).
7. Remove the now-empty `scratch/{slug}/` directory.

## Phase 2: Deterministic Scraper Generation

### Create Scraper Directory

The `{scraper-name}/` directory already exists (created
during the transition step) and contains `traces/{slug}/` with the Phase 1
artifacts. Create the `output/` and `__tests__/` subdirectories.

### Design Integration Tests First

Create integration tests in `__tests__/` that:
- Run Playwright against the live URL
- Verify output correctness based on what you observed in Phase 1
- Check output shape, non-empty fields, and structural invariants

**Present the tests to the user and get confirmation before implementing the
scraper.**

### Implement the Scraper

Read the Phase 1 trace artifacts from `{scraper-name}/traces/{slug}/`
(metadata, trace, narrative, and network requests).

Write the scraper in TypeScript. Requirements:

- **Standalone**: Runs with just Playwright. No Claude Code, no MCP, no LLM
  dependencies (minimize LLM-powered handles).
- **Exhaustive iteration**: Unlike Phase 1, the deterministic scraper should
  process every loop iteration to completion (all pages, all items, etc.). Use
  the loop pattern captured in the traces and narrative to implement exhaustive
  iteration with proper termination conditions.
- **Output**: `console.log` the extracted content to STDOUT, and also write it
  to `{scraper-name}/output/`.
- **Human-like delays**: Bake in random delays between actions (e.g., 500-2000ms).
- **Network optimization**: Check the captured network request files. If the
  site uses a JSON API, prefer direct HTTP/fetch requests. The scraper may still
  load the page in a browser first to grab cookies or session tokens.
- **File structure**: Use a single `index.ts` or split into multiple files based
  on complexity. Make your own judgment per scraper.
- **On failure**: The scraper should simply fail with an error if the site has
  changed in a breaking way. No auto-recovery.

### Test and Iterate

Validate using:
1. Your integration tests
2. A fresh Playwright MCP navigation to the URL to compare output

If anything breaks during testing, iterate on the scraper code until it works.

## Important Notes

- Auth is out of scope. Do not handle login flows or authenticated content.
- Every `/scrape` invocation starts fresh. Do not reuse traces from previous runs.
- Use ultrathink for complex navigation decisions and scraper design.
