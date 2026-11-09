# Test Cases: Agent Reach Platform Approaches for Linky

## Source

- Feature spec: ../features/agent-reach-platforms.md

## Acceptance Tests

1. **Strategy loads platform providers**
   - Given a strategy file with platform provider definitions
   - When Linky loads the strategy
   - Then each provider exposes id, method, requirements, route role, and
     fallback metadata without hard-coded defaults overriding the file.

2. **Platform route jumps to native provider**
   - Given a YouTube, GitHub, V2EX, Bilibili, Reddit, XiaoHongShu, Xueqiu, or
     RSS URL
   - When domain planning runs
   - Then Linky selects the platform route before the generic Jina/trafilatura/
     Scrapling chain.

3. **Missing CLI is skipped with trace**
   - Given a platform provider depends on a command that is not installed
   - When extraction reaches that provider
   - Then the link is routed to the next valid fallback or marked blocked/failed
     with a trace entry naming the missing requirement.

4. **Install check reports auto-installable dependencies**
   - Given `bin/install --check` or equivalent safe mode runs
   - When platform providers are enabled
   - Then it reports missing `yt-dlp`, `gh`, `feedparser`, `bili`,
     `twitter`, `rdt`, `opencli`, `mcporter`, and `ffmpeg` support with
     clear auto/manual actions.

5. **Doctor reports provider readiness**
   - Given a strategy with platform providers
   - When `bin/linky-doctor` runs
   - Then provider readiness includes commands, Python modules, MCP config,
     user-visible session requirements, and missing credential/config warnings.

6. **YouTube transcript provider normalizes output**
   - Given `yt-dlp` returns real-shaped `requested_subtitles` metadata and a
     selected subtitle URL returns JSON3 events
   - When the provider parses it
   - Then Linky emits Markdown transcript content plus metadata for title,
     author/channel, duration, upload date, and source URL.

7. **GitHub provider uses gh output**
   - Given `gh` returns repository, issue, or PR JSON
   - When the provider parses it
   - Then Linky emits concise Markdown and structured metadata without raw
     command noise.

8. **V2EX public API provider parses topics and replies**
   - Given V2EX topic and reply JSON fixtures
   - When the provider parses them
   - Then title, author, node, content, replies, created time, and URL are
     preserved.

9. **XiaoHongShu result cleaner strips redundant fields**
   - Given a nested note/search response fixture
   - When the provider normalizes it
   - Then only useful note id, title, description/content, author, engagement,
     tags, image URLs, and comments remain.

10. **Unimplemented providers are identified honestly**
    - Given a session-backed provider has only a strategy definition
    - When doctor and extraction run, even with every dependency present
    - Then doctor reports `implemented: false` and `unimplemented`; extraction
      records `provider not implemented` and follows the configured fallback.
    - Authenticated extraction and live service health remain unverified until
      an actual adapter and its session checks exist.

11. **Native extraction respects target and resource boundaries**
    - A GitHub file/tree/release URL never returns a repository summary as its
      extracted body; the failed attempt is traced and the next provider runs.
    - Recognizable feed paths select feedparser without overriding explicit
      domain routes; feed retrieval has a timeout and rejects non-feed data.
    - Missing/empty captions never produce a successful video transcript.
    - Disabled providers are not invoked; all Markdown respects `max_chars`.

12. **Install status reflects actual results**
    - A nonzero install command, missing package manager or manual-only
      dependency leaves a nonzero exit status and an actionable message.
    - A command returning zero without making its dependency available still
      fails the post-install check.
    - Successful installation is verified for both commands and Python modules;
      `--check` never invokes an installer.

## Edge Cases

- A platform CLI is installed but broken because its virtualenv interpreter or
  Node runtime is missing.
- A command exists but exits non-zero to signal unauthenticated state rather than
  tool failure.
- A browser extension is installed but asleep; readiness should distinguish
  installed-but-sleeping from not installed.
- A public API returns HTTP 403, empty data, or access-denied content.
- A shortlink expands to a platform URL after domain planning.
- Search-only providers such as Exa should never claim to have read a URL.
- Bilibili should not route to `yt-dlp` for B站 extraction.
- Session/token values must never appear in trace, doctor, or reports.

## Regression Tests

- Existing Jina, trafilatura, Scrapling, WebFetch, browser, and vxTwitter
  routes still load.
- Existing `scripts/scrapling_fetch.py <url> [max_chars]` remains compatible.
- Existing unit tests for strategy loading, extraction contracts, graph, report,
  source intake, and doctor still pass.
- Existing docs and examples do not claim Agent Reach is a Linky runtime
  dependency.
