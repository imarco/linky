# Agent Reach Platform Approaches Design

## Context

Linky already has a local extraction pipeline driven by
`references/fetch-strategy.toml`, with provider fallback, domain routes,
quality scoring, extraction traces, and report assembly. The current platform
coverage is mostly generic webpage extraction plus a dedicated vxTwitter
provider.

Agent Reach is useful here as a researched catalog of working platform
approaches. Linky should absorb those approaches directly as native providers,
not depend on Agent Reach as a runtime router.

## Recommended Design

Use a thin native provider expansion inside Linky:

1. Extend strategy metadata so providers can declare command, Python module,
   JSON API, MCP, transcript, search-only, and user-visible-session behavior.
2. Add platform domain routes for YouTube, GitHub, RSS, Exa search, V2EX,
   Bilibili, Twitter/X, Reddit, XiaoHongShu, LinkedIn, Xueqiu, and Xiaoyuzhou.
3. Add small parser functions that convert upstream CLI/API output into
   `ExtractionResult` metadata and readable Markdown.
4. Extend doctor/install support so Linky owns dependency checks and safe
   user-space installation guidance.

This keeps Linky's runtime simple: one strategy file, one extraction contract,
one doctor surface, one install surface.

## Alternatives Considered

### Runtime adapter to Agent Reach

Rejected. It would make Linky's behavior depend on a second router, duplicate
trace decisions, and make `bin/install` less authoritative.

### Vendor Agent Reach channel code

Rejected. It imports another project's class structure and maintenance
assumptions. Linky only needs the platform approaches and parsers shaped for
its own contracts.

### Native provider expansion

Chosen. It fits existing Linky contracts, keeps tests local, and lets each
platform approach be added behind domain routes with explicit readiness checks.

## Platform Provider Map

| Platform | Provider ids | Notes |
|---|---|---|
| Generic web | `jina`, `trafilatura`, `scrapling`, `webfetch`, `browser` | Existing chain stays intact. |
| YouTube | `youtube_ytdlp` | Metadata and subtitles through `yt-dlp`; JS runtime readiness checked. |
| GitHub | `github_gh` | Repos, issues, PRs, releases, code search through `gh`. |
| RSS / Atom | `rss_feedparser` | Feed URLs and feed discovery through `feedparser`. |
| Exa search | `exa_search` | Search-only follow-up provider through `mcporter`. |
| V2EX | `v2ex_api` | Public JSON APIs. |
| Bilibili | `bilibili_cli`, `opencli_bilibili` | `bili-cli` first; no Bilibili `yt-dlp` path. |
| Twitter / X | `vxtwitter`, `twitter_cli`, `opencli_twitter` | Keep public status route, add richer logged-in routes. |
| Reddit | `opencli_reddit`, `rdt_cli` | Login-required, fail closed when no session exists. |
| XiaoHongShu | `opencli_xhs`, `xiaohongshu_mcp`, `xhs_cli` | Desktop, server, legacy order. |
| LinkedIn | `linkedin_jina`, `linkedin_mcp` | Public pages via Jina, full features only with MCP config. |
| Xueqiu | `xueqiu_api` | Cookie-aware API client, no secret trace output. |
| Xiaoyuzhou | `xiaoyuzhou_transcript` | Audio transcript path with `ffmpeg` and configured transcription provider. |

## Boundaries

- No `agent-reach` command calls.
- No cloned upstream tool repos inside the Linky workspace.
- No sudo from install scripts.
- No write actions on social platforms.
- Login-required providers only read user-visible content or configured sessions.
- Traces and doctor reports never include saved sessions, tokens, or browser state.

## Open Questions

- None
