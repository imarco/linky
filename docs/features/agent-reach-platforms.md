# Agent Reach Platform Approaches for Linky

## Problem

Linky already has a local extraction pipeline with strategy-driven fallback,
domain routes, trace output, and a doctor. Its current platform coverage is
still weighted toward generic webpage extraction: Jina, trafilatura, Scrapling,
WebFetch, browser snapshots, and one dedicated vxTwitter provider.

Agent Reach's useful contribution is not its runtime package. The value is the
platform-by-platform approach catalog: use the upstream tool or public API that
currently works best for each site, probe it honestly, and route directly to it
instead of wasting tokens and quota on generic webpage readers.

This subproject absorbs those platform approaches into Linky's native provider
model and install flow. Linky should not depend on Agent Reach at runtime and
should not wrap the Agent Reach CLI as an adapter.

## Goals

- Add native Linky provider definitions for high-value platform approaches
  derived from Agent Reach's current upstream choices.
- Extend domain routes so platform URLs jump directly to the right provider or
  ordered provider set.
- Extend the install and doctor surface so required CLIs/modules are detected
  and can be installed from Linky's own bin/install workflow.
- Normalize platform-specific CLI/API output into Linky's existing
  `ExtractionResult`, `ExtractionTrace`, `ReportData`, and research graph
  contracts.
- Preserve Linky's existing lightweight local pipeline: no online service, no
  package publishing, no opaque runtime dependency on Agent Reach.

## Non-goals

- Do not add Agent Reach as a runtime dependency.
- Do not shell out to `agent-reach doctor` or `agent-reach install` as the
  implementation path.
- Do not vendor the Agent Reach repository or clone its channel classes.
- Do not implement posting, commenting, liking, following, or any write action.
- Do not access login walls, paywalls, CAPTCHA, account restrictions, or content
  the user cannot already access.
- Do not add every optional platform in one risky implementation phase if a
  smaller provider slice gives testable value first.

## Scope and Boundaries

### Platform approaches to absorb

| Platform / URL class | Linky native provider direction | Install / doctor dependency |
|---|---|---|
| Generic web pages | Keep Jina Reader as a clean Markdown provider and preserve current generic fallback chain. | none beyond existing network access |
| YouTube | Add a `yt-dlp` provider for metadata, captions, and transcript extraction; require a JS runtime when YouTube extraction needs it. | `yt-dlp`, `node` or `deno`, optional `ffmpeg` for audio transcription |
| GitHub | Add a `gh` provider for repo, issue, PR, release, and code search contexts before falling back to webpage extraction. | `gh` |
| RSS / Atom | Add a feed provider for feed URLs and feed discovery where cheap. | Python `feedparser` |
| Exa search | Add a search-only follow-up provider for research gap filling, not direct URL reading. | `mcporter` with Exa MCP config |
| V2EX | Add a public API provider for topics, nodes, users, and replies; search remains external search or site URL fallback. | none beyond Python stdlib HTTP |
| Bilibili | Add `bili-cli` as the first provider for search, hot/ranking, and video detail; use OpenCLI only for browser-session subtitle paths. | `bili`, optional `opencli` |
| Twitter / X | Keep vxTwitter/FixTweet for public status URLs where it is sufficient; add `twitter-cli` and optional OpenCLI paths for search, timelines, articles, and threads. | `twitter`, optional `opencli` |
| Reddit | Treat as login-required. Add OpenCLI / `rdt-cli` provider options only when a valid user-visible session is configured. | optional `opencli` or `rdt` |
| XiaoHongShu | Replace generic browser-only route with ordered native options: OpenCLI on desktop, `xiaohongshu-mcp` on server, legacy `xhs-cli` only if already present. | optional `opencli`, `mcporter`, `xhs` |
| LinkedIn | Use Jina for public pages; add MCP-backed provider for profiles/jobs only when explicitly configured. | optional `linkedin-scraper-mcp`, `mcporter` |
| Xueqiu | Add a session-aware public API provider for stock quotes, search, hot posts, and hot stocks. | optional saved session support |
| Xiaoyuzhou | Add a podcast transcript provider using audio download, ffmpeg slicing, and Whisper-compatible transcription. | `ffmpeg`, configured transcription key/provider |

### Implementation boundaries

- Provider code belongs under `scripts/linky/` runtime modules.
- User-facing install and doctor entrypoints belong under `bin/`.
- Strategy, domain routes, provider metadata, install hints, and dependency
  requirements remain data-driven where practical.
- Each new provider must return structured data and trace information, not raw
  CLI dumps.
- Logged-in providers must be opt-in and clearly marked as user-visible session
  providers.

## UX / API Contract

### Strategy contract

`references/fetch-strategy.toml` should describe:

- provider id, method, command/API mode, requirements, and best_for notes
- domain routes for platform URLs
- whether the provider is `url-reader`, `search-only`, `transcript`, or
  `user-visible-session`
- fallback behavior when a provider is missing, unauthenticated, blocked, or
  returns low-quality content

### Install contract

`bin/install` should support:

- safe dependency checks with no system changes unless requested
- automatic installation for user-space dependencies where safe, such as pipx,
  npm global tools, and Python modules
- clear manual instructions for browser extensions, saved sessions, API keys, and MCP
  services
- no sudo without explicit user approval
- no cloned tool repositories inside the Linky workspace

### Doctor contract

`bin/linky-doctor` should report:

- provider readiness by id
- missing command/module/config per provider
- whether a missing dependency is auto-installable or manual
- platform route readiness for major domains
- no secret values, tokens, saved sessions, or sensitive browser state

### Extraction contract

Each platform provider maps upstream output into:

- `status`: `success`, `partial`, `blocked`, or `failed`
- `provider`: stable Linky provider id
- `markdown`: readable normalized content when available
- `metadata`: platform-specific structured fields, stripped to useful data
- `quality`: provider-specific quality score
- `trace`: command/API attempts, elapsed time, skipped fallback reasons
- `errors`: bounded, non-secret failure details

## Open Questions

- None
