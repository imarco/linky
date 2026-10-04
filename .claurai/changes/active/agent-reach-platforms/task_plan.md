# Agent Reach Platform Approaches Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Absorb Agent Reach's platform data-access approaches into Linky's native provider, domain route, doctor, and install surfaces.

**Architecture:** Keep Linky's existing extraction contract as the single runtime shape. Add small native providers and parser helpers under `scripts/linky/`, describe them in `references/fetch-strategy.toml`, and expose dependency checks through `bin/install` plus `bin/linky-doctor`.

**Tech Stack:** Python stdlib, unittest, TOML strategy config, optional CLI tools (`yt-dlp`, `gh`, `bili`, `twitter`, `rdt`, `opencli`, `mcporter`, `ffmpeg`), optional Python modules (`feedparser`).

---

## Plan Review Decisions

Full plan review on 2026-07-01 accepted the overall native-provider direction,
but tightened the execution boundary:

- Phase 1 must not count missing-tool placeholders as platform absorption. It
  must ship a real zero-login vertical slice for YouTube, GitHub, RSS, and V2EX,
  with command/API execution, parser normalization, trace, and tests.
- Login/session-heavy providers remain route metadata plus fail-closed readiness
  in this phase unless a configured user-visible session exists.
- `bin/install` must prefer user-space installers such as `pipx`/safe module
  installs and report manual dependencies clearly. It must not rely only on
  `pip install --user`, because modern Python installs may reject that path.
- Provider completion is defined by structured `ExtractionResult` output and
  trace, not by strategy metadata alone.

## File Structure

- Modify `references/fetch-strategy.toml`: add platform provider metadata and domain routes.
- Modify `scripts/linky/strategy.py`: expose provider requirements from both fallback and dedicated provider sections.
- Create `scripts/linky/providers/platforms.py`: parser, command-building, and zero-login provider helpers for platform providers.
- Modify `scripts/linky/extract.py`: register platform provider functions behind provider ids.
- Modify `scripts/linky/doctor.py`: report commands/modules/config readiness for all provider sections.
- Create `bin/install`: user-facing dependency check/install script, safe by default.
- Create `bin/linky-doctor`: user-facing wrapper that imports `scripts/linky/doctor.py`.
- Modify `README.md`: document native platform providers and clarify Agent Reach is only a research source.
- Modify tests:
  - `tests/test_strategy_and_extraction.py`
  - `tests/test_source_intake_and_doctor.py`
  - Create `tests/test_platform_providers.py`

### Phase 1: Strategy, parser, and route metadata foundation
- **Status:** complete

### Task 1: Strategy Provider Metadata

**Files:**
- Modify: `references/fetch-strategy.toml`
- Modify: `scripts/linky/strategy.py`
- Test: `tests/test_strategy_and_extraction.py`

- [x] **Step 1: Write failing strategy tests**

Add these tests to `tests/test_strategy_and_extraction.py`:

```python
    def test_provider_config_reads_dedicated_platform_provider(self):
        provider = self.strategy["providers"]["youtube_ytdlp"]

        self.assertEqual(provider["method"], "command-json")
        self.assertIn("yt-dlp", provider["requires"])
        self.assertEqual(provider["role"], "transcript")

    def test_youtube_domain_route_prefers_ytdlp_provider(self):
        chain = resolve_provider_chain("https://www.youtube.com/watch?v=dQw4w9WgXcQ", self.strategy)

        self.assertEqual(chain[0], "youtube_ytdlp")
        self.assertNotIn("jina", chain[:1])

    def test_bilibili_route_never_uses_ytdlp(self):
        chain = resolve_provider_chain("https://www.bilibili.com/video/BV123", self.strategy)

        self.assertEqual(chain[0], "bilibili_cli")
        self.assertNotIn("youtube_ytdlp", chain)
```

- [x] **Step 2: Run tests to verify failure**

Run:

```bash
python3 -m unittest tests.test_strategy_and_extraction
```

Expected: FAIL because `youtube_ytdlp` and `bilibili_cli` are not present in strategy routes.

- [x] **Step 3: Add platform providers to strategy**

Add dedicated provider sections to `references/fetch-strategy.toml`:

```toml
[providers.youtube_ytdlp]
name = "YouTube yt-dlp"
method = "command-json"
role = "transcript"
command = "yt-dlp --dump-single-json --skip-download --write-auto-subs --sub-lang {sub_lang} {url}"
best_for = "YouTube metadata, captions, subtitles, and transcript extraction"
notes = "Requires yt-dlp plus node or deno for current YouTube extraction paths"
requires = ["yt-dlp", "node-or-deno"]

[providers.github_gh]
name = "GitHub gh CLI"
method = "command-json"
role = "structured-url-reader"
best_for = "GitHub repositories, issues, pull requests, releases, and code search"
requires = ["gh"]

[providers.rss_feedparser]
name = "RSS feedparser"
method = "python"
role = "feed"
best_for = "RSS and Atom feeds"
requires = ["feedparser"]

[providers.exa_search]
name = "Exa Search via mcporter"
method = "mcp-command"
role = "search-only"
best_for = "Research follow-up search and code context lookup"
requires = ["mcporter", "exa-mcp-config"]

[providers.v2ex_api]
name = "V2EX public API"
method = "json-api"
role = "structured-url-reader"
best_for = "V2EX topics, nodes, replies, and users"
requires = []

[providers.bilibili_cli]
name = "Bilibili bili-cli"
method = "command-json"
role = "structured-url-reader"
best_for = "Bilibili search, hot/ranking, and video detail"
requires = ["bili"]

[providers.opencli_bilibili]
name = "OpenCLI Bilibili"
method = "command-yaml"
role = "user-visible-session"
best_for = "Bilibili subtitles through browser session"
requires = ["opencli"]

[providers.twitter_cli]
name = "twitter-cli"
method = "command-json"
role = "user-visible-session"
best_for = "X/Twitter search, timeline, articles, and threads"
requires = ["twitter"]

[providers.opencli_twitter]
name = "OpenCLI Twitter"
method = "command-yaml"
role = "user-visible-session"
best_for = "Twitter through user's Chrome session"
requires = ["opencli"]

[providers.opencli_reddit]
name = "OpenCLI Reddit"
method = "command-yaml"
role = "user-visible-session"
best_for = "Reddit search, posts, comments through browser session"
requires = ["opencli"]

[providers.rdt_cli]
name = "rdt-cli"
method = "command-json"
role = "user-visible-session"
best_for = "Reddit search and post reading with imported saved sessions"
requires = ["rdt"]

[providers.opencli_xhs]
name = "OpenCLI XiaoHongShu"
method = "command-yaml"
role = "user-visible-session"
best_for = "XiaoHongShu desktop reading through Chrome session"
requires = ["opencli"]

[providers.xiaohongshu_mcp]
name = "xiaohongshu-mcp"
method = "mcp-command"
role = "user-visible-session"
best_for = "XiaoHongShu server/headless reading after QR login"
requires = ["mcporter", "xiaohongshu-mcp-service"]

[providers.xhs_cli]
name = "xhs-cli legacy"
method = "command-json"
role = "user-visible-session"
best_for = "Existing xhs-cli installs only"
requires = ["xhs"]

[providers.linkedin_mcp]
name = "LinkedIn MCP"
method = "mcp-command"
role = "user-visible-session"
best_for = "LinkedIn profile, company, and job search"
requires = ["mcporter", "linkedin-mcp-config"]

[providers.xueqiu_api]
name = "Xueqiu API"
method = "json-api"
role = "user-visible-session"
best_for = "Xueqiu stock quotes, search, hot posts, and hot stocks"
requires = ["xueqiu-session"]

[providers.xiaoyuzhou_transcript]
name = "Xiaoyuzhou transcript"
method = "command-transcript"
role = "transcript"
best_for = "Xiaoyuzhou podcast audio transcription"
requires = ["ffmpeg", "transcription-provider"]
```

Add routes:

```toml
[[domain_routes]]
pattern = "youtube.com"
go_to = "youtube_ytdlp"
skip_layers = ["jina", "trafilatura", "scrapling", "webfetch"]
reason = "YouTube content is better extracted through yt-dlp metadata and subtitle APIs"

[[domain_routes]]
pattern = "youtu.be"
go_to = "youtube_ytdlp"
skip_layers = ["jina", "trafilatura", "scrapling", "webfetch"]
reason = "YouTube short URLs should use yt-dlp provider"

[[domain_routes]]
pattern = "github.com"
go_to = "github_gh"
skip_layers = []
reason = "GitHub structured data is available through gh CLI before webpage fallback"

[[domain_routes]]
pattern = "bilibili.com"
go_to = "bilibili_cli"
skip_layers = ["jina", "trafilatura", "scrapling", "webfetch", "youtube_ytdlp"]
reason = "Bilibili should use bili-cli or OpenCLI, not yt-dlp"

[[domain_routes]]
pattern = "v2ex.com"
go_to = "v2ex_api"
skip_layers = ["jina"]
reason = "V2EX public JSON APIs provide structured topic and reply data"

[[domain_routes]]
pattern = "reddit.com"
go_to = "opencli_reddit"
skip_layers = ["jina", "trafilatura", "scrapling", "webfetch"]
reason = "Reddit has no zero-config public path and requires user-visible login"

[[domain_routes]]
pattern = "xiaohongshu.com"
go_to = "opencli_xhs"
skip_layers = ["jina", "trafilatura", "scrapling", "webfetch"]
reason = "XiaoHongShu requires browser-visible or configured session providers"

[[domain_routes]]
pattern = "xhslink.com"
go_to = "opencli_xhs"
skip_layers = ["jina", "trafilatura", "scrapling", "webfetch"]
reason = "XiaoHongShu short links require the same session-aware providers"

[[domain_routes]]
pattern = "linkedin.com"
go_to = "linkedin_mcp"
skip_layers = []
reason = "LinkedIn public pages may fallback to Jina, full profile/job data needs MCP"

[[domain_routes]]
pattern = "xueqiu.com"
go_to = "xueqiu_api"
skip_layers = ["jina", "trafilatura", "scrapling", "webfetch"]
reason = "Xueqiu structured data is available through session-aware APIs"

[[domain_routes]]
pattern = "xiaoyuzhoufm.com"
go_to = "xiaoyuzhou_transcript"
skip_layers = ["jina", "trafilatura", "scrapling", "webfetch"]
reason = "Podcast value comes from audio transcript extraction"
```

- [x] **Step 4: Run strategy tests**

Run:

```bash
python3 -m unittest tests.test_strategy_and_extraction
```

Expected: PASS for new route tests and existing fallback tests.

- [x] **Step 5: Commit**

```bash
git add references/fetch-strategy.toml tests/test_strategy_and_extraction.py
git commit -m "feat(strategy): add platform provider routes"
```

### Task 2: Platform Parser Helpers

**Files:**
- Create: `scripts/linky/providers/platforms.py`
- Create: `tests/test_platform_providers.py`

- [x] **Step 1: Write parser tests**

Create `tests/test_platform_providers.py`:

```python
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from linky.providers.platforms import (
    clean_xhs_note,
    github_repo_to_markdown,
    v2ex_topic_to_markdown,
    youtube_info_to_markdown,
)


class PlatformProviderParserTests(unittest.TestCase):
    def test_youtube_info_to_markdown_keeps_transcript_and_metadata(self):
        markdown, metadata = youtube_info_to_markdown(
            {
                "title": "Demo Video",
                "channel": "Example Channel",
                "duration": 120,
                "upload_date": "20260626",
                "webpage_url": "https://www.youtube.com/watch?v=abc",
                "subtitles_text": "Hello from captions.",
            }
        )

        self.assertIn("# Demo Video", markdown)
        self.assertIn("Hello from captions.", markdown)
        self.assertEqual(metadata["channel"], "Example Channel")
        self.assertEqual(metadata["duration"], 120)

    def test_github_repo_to_markdown_keeps_repo_fields(self):
        markdown, metadata = github_repo_to_markdown(
            {
                "nameWithOwner": "imarco/linky",
                "description": "Link research tool",
                "url": "https://github.com/imarco/linky",
                "stargazerCount": 42,
                "primaryLanguage": {"name": "Python"},
            }
        )

        self.assertIn("# imarco/linky", markdown)
        self.assertIn("Link research tool", markdown)
        self.assertEqual(metadata["stars"], 42)

    def test_v2ex_topic_to_markdown_keeps_replies(self):
        markdown, metadata = v2ex_topic_to_markdown(
            {
                "id": 123,
                "title": "Python discussion",
                "content": "Topic body",
                "url": "https://www.v2ex.com/t/123",
                "member": {"username": "alice"},
                "node": {"name": "python", "title": "Python"},
                "replies": [
                    {"author": "bob", "content": "Reply text", "created": 1},
                ],
            }
        )

        self.assertIn("# Python discussion", markdown)
        self.assertIn("Reply text", markdown)
        self.assertEqual(metadata["node_name"], "python")

    def test_clean_xhs_note_strips_redundant_fields(self):
        cleaned = clean_xhs_note(
            {
                "note_card": {
                    "note_id": "n1",
                    "title": "Title",
                    "desc": "Body",
                    "user": {"nickname": "Alice", "user_id": "u1", "avatar": "drop"},
                    "interact_info": {"liked_count": 5, "ignored": 1},
                    "image_list": [{"url": "https://img"}],
                    "tag_list": [{"name": "tag"}],
                },
                "massive": {"ignored": True},
            }
        )

        self.assertEqual(cleaned["note_id"], "n1")
        self.assertEqual(cleaned["user"]["nickname"], "Alice")
        self.assertNotIn("massive", cleaned)
```

- [x] **Step 2: Run tests to verify failure**

Run:

```bash
python3 -m unittest tests.test_platform_providers
```

Expected: FAIL with import error for `linky.providers.platforms`.

- [x] **Step 3: Add minimal parser helpers**

Create `scripts/linky/providers/platforms.py`:

```python
from __future__ import annotations

from typing import Any


def youtube_info_to_markdown(info: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    title = str(info.get("title") or "YouTube video").strip()
    channel = str(info.get("channel") or info.get("uploader") or "").strip()
    url = str(info.get("webpage_url") or info.get("original_url") or "").strip()
    subtitles = str(info.get("subtitles_text") or info.get("automatic_captions_text") or "").strip()
    duration = info.get("duration")
    upload_date = str(info.get("upload_date") or "").strip()

    lines = [f"# {title}", ""]
    if channel:
        lines.append(f"Channel: {channel}")
    if upload_date:
        lines.append(f"Upload date: {upload_date}")
    if duration is not None:
        lines.append(f"Duration seconds: {duration}")
    if url:
        lines.append(f"Source: [{url}]({url})")
    lines.append("")
    if subtitles:
        lines.extend(["## Transcript", "", subtitles, ""])

    metadata = {
        "title": title,
        "channel": channel,
        "duration": duration,
        "upload_date": upload_date,
        "source_url": url,
        "content_type": "video_transcript",
    }
    return "\n".join(lines).strip() + "\n", _compact(metadata)


def github_repo_to_markdown(repo: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    name = str(repo.get("nameWithOwner") or repo.get("full_name") or repo.get("name") or "GitHub repository")
    description = str(repo.get("description") or "").strip()
    url = str(repo.get("url") or repo.get("html_url") or "").strip()
    language = repo.get("primaryLanguage")
    if isinstance(language, dict):
        language = language.get("name")
    stars = repo.get("stargazerCount", repo.get("stars", repo.get("stargazers_count")))

    lines = [f"# {name}", ""]
    if description:
        lines.extend([description, ""])
    if language:
        lines.append(f"- Language: {language}")
    if stars is not None:
        lines.append(f"- Stars: {stars}")
    if url:
        lines.append(f"- Source: [{url}]({url})")

    metadata = {"name": name, "description": description, "url": url, "language": language, "stars": stars}
    return "\n".join(lines).strip() + "\n", _compact(metadata)


def v2ex_topic_to_markdown(topic: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    title = str(topic.get("title") or "V2EX topic").strip()
    content = str(topic.get("content") or "").strip()
    url = str(topic.get("url") or "").strip()
    member = topic.get("member") if isinstance(topic.get("member"), dict) else {}
    node = topic.get("node") if isinstance(topic.get("node"), dict) else {}
    replies = topic.get("replies") if isinstance(topic.get("replies"), list) else []

    lines = [f"# {title}", ""]
    if member.get("username"):
        lines.append(f"Author: {member['username']}")
    if node.get("title") or node.get("name"):
        lines.append(f"Node: {node.get('title') or node.get('name')}")
    if url:
        lines.append(f"Source: [{url}]({url})")
    if content:
        lines.extend(["", content])
    if replies:
        lines.extend(["", "## Replies", ""])
        for reply in replies:
            if not isinstance(reply, dict):
                continue
            author = reply.get("author") or reply.get("username") or "unknown"
            body = str(reply.get("content") or "").strip()
            if body:
                lines.append(f"- {author}: {body}")

    metadata = {
        "id": topic.get("id"),
        "node_name": node.get("name"),
        "node_title": node.get("title"),
        "author": member.get("username"),
        "reply_count": len(replies),
        "url": url,
    }
    return "\n".join(lines).strip() + "\n", _compact(metadata)


def clean_xhs_note(note: Any) -> Any:
    if isinstance(note, list):
        return [clean_xhs_note(item) for item in note]
    if not isinstance(note, dict):
        return note

    inner = note.get("note_card") or note.get("note") or note
    if not isinstance(inner, dict):
        return note

    result: dict[str, Any] = {}
    for key in ("id", "note_id", "xsec_token", "title", "desc", "content", "type", "time"):
        if inner.get(key) not in (None, ""):
            result[key] = inner[key]

    user = inner.get("user") or inner.get("author")
    if isinstance(user, dict):
        result["user"] = {k: user[k] for k in ("nickname", "user_id", "nick_name") if k in user}

    interact = inner.get("interact_info") or inner.get("note_interact_info") or {}
    if isinstance(interact, dict):
        for key in ("liked_count", "collected_count", "comment_count", "share_count"):
            if key in interact:
                result[key] = interact[key]

    images = inner.get("image_list") or inner.get("images_list") or []
    if isinstance(images, list):
        urls = []
        for image in images:
            if isinstance(image, dict):
                url = image.get("url") or image.get("url_default") or image.get("original")
                if url:
                    urls.append(url)
            elif isinstance(image, str):
                urls.append(image)
        if urls:
            result["images"] = urls

    tags = inner.get("tag_list") or inner.get("tags") or []
    if isinstance(tags, list):
        names = [tag.get("name") for tag in tags if isinstance(tag, dict) and tag.get("name")]
        names.extend(tag for tag in tags if isinstance(tag, str))
        if names:
            result["tags"] = names

    return result


def _compact(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value not in (None, "", [])}
```

- [x] **Step 4: Run parser tests**

Run:

```bash
python3 -m unittest tests.test_platform_providers
```

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add scripts/linky/providers/platforms.py tests/test_platform_providers.py
git commit -m "feat(providers): add platform output parsers"
```

### Phase 2: Zero-login native provider vertical slice
- **Status:** complete

### Task 3: Native Provider Execution

**Files:**
- Modify: `scripts/linky/extract.py`
- Modify: `scripts/linky/providers/platforms.py`
- Modify: `tests/test_strategy_and_extraction.py`
- Modify: `tests/test_platform_providers.py`

- [x] **Step 1: Write failing extraction tests**

Add provider execution tests to `tests/test_strategy_and_extraction.py` and parser fixtures to
`tests/test_platform_providers.py`:

```python
    def test_platform_provider_can_be_registered_by_id(self):
        def youtube_provider(url, provider, strategy):
            return {
                "markdown": "# Video\n\nTranscript with enough source metadata.\n\nPublished by Example.\n\n[source](https://youtu.be/x)",
                "metadata": {"provider": "youtube_ytdlp"},
            }

        strategy = {
            "global": {"quality_threshold": 0.55},
            "quality": {"min_score": 0.55},
            "providers": {"youtube_ytdlp": {"id": "youtube_ytdlp"}},
            "domain_routes": [{"pattern": "youtube.com", "go_to": "youtube_ytdlp", "skip_layers": ["jina"]}],
            "fallback_chain": [{"id": "jina"}],
        }

        result = extract_url(
            "https://www.youtube.com/watch?v=x",
            strategy=strategy,
            providers={"youtube_ytdlp": youtube_provider},
        )

        self.assertEqual(result.status, "success")
        self.assertEqual(result.provider, "youtube_ytdlp")

    def test_youtube_provider_runs_ytdlp_and_normalizes_output(self):
        # Inject a command runner that returns yt-dlp JSON with subtitles_text.
        # Assert ExtractionResult.provider == "youtube_ytdlp", status success,
        # markdown contains transcript, and trace records the provider attempt.
        ...

    def test_github_provider_runs_gh_and_normalizes_repo_output(self):
        # Inject a command runner that returns gh JSON for a repository URL.
        # Assert Markdown + metadata use normalized repo fields.
        ...

    def test_rss_provider_uses_feedparser_when_available(self):
        # Inject feedparser-style parsed data and assert feed entries are rendered.
        ...

    def test_v2ex_provider_fetches_topic_and_replies(self):
        # Inject HTTP JSON responses for topic and replies and assert replies are preserved.
        ...
```

- [x] **Step 2: Run test to verify current behavior**

Run:

```bash
python3 -m unittest tests.test_strategy_and_extraction.StrategyAndExtractionTests.test_platform_provider_can_be_registered_by_id
```

Expected: injected-provider registration may already pass, but the real
YouTube/GitHub/RSS/V2EX provider tests must fail until provider execution is
implemented.

- [x] **Step 3: Implement real zero-login providers**

Modify `scripts/linky/providers/platforms.py` and `scripts/linky/extract.py` so the first
zero-login slice performs actual extraction:

```python
DEFAULT_PROVIDERS: dict[str, ProviderFn] = {
    "jina": _http_markdown,
    "webfetch": _http_markdown,
    "trafilatura": _trafilatura_provider,
    "scrapling": _scrapling_provider,
    "vxtwitter": _vxtwitter_provider,
    "browser": _command_provider,
    "youtube_ytdlp": _youtube_ytdlp_provider,
    "github_gh": _github_gh_provider,
    "rss_feedparser": _rss_feedparser_provider,
    "v2ex_api": _v2ex_api_provider,
    # Session/config-heavy providers fail closed until their dependencies are ready.
    "exa_search": _missing_or_unconfigured_provider("mcporter exa"),
    "bilibili_cli": _missing_or_unconfigured_provider("bili"),
    "opencli_bilibili": _missing_or_unconfigured_provider("opencli"),
    "twitter_cli": _missing_or_unconfigured_provider("twitter"),
    "opencli_twitter": _missing_or_unconfigured_provider("opencli"),
    "opencli_reddit": _missing_or_unconfigured_provider("opencli"),
    "rdt_cli": _missing_or_unconfigured_provider("rdt"),
    "opencli_xhs": _missing_or_unconfigured_provider("opencli"),
    "xiaohongshu_mcp": _missing_or_unconfigured_provider("mcporter xiaohongshu"),
    "xhs_cli": _missing_or_unconfigured_provider("xhs"),
    "linkedin_mcp": _missing_or_unconfigured_provider("mcporter linkedin"),
    "xueqiu_api": _missing_or_unconfigured_provider("xueqiu-session"),
    "xiaoyuzhou_transcript": _missing_or_unconfigured_provider("ffmpeg/transcription-provider"),
}
```

Provider requirements:

- YouTube: run `yt-dlp --dump-single-json --skip-download`, collect available
  subtitles/automatic captions when present, and map to `youtube_info_to_markdown`.
- GitHub: classify repo/issue/PR/release URLs, call `gh api` or `gh repo view --json`
  as appropriate, and map JSON to concise Markdown.
- RSS: import `feedparser`, parse feed URL, and render feed title plus entries.
- V2EX: use stdlib HTTP for topic metadata and replies; no command dependency.
- All command/API helpers must accept injectable runners/fetchers in tests so unit
  tests do not require external CLIs, credentials, or network.
- Missing commands/modules/config return failed or blocked trace entries with
  bounded messages and no secrets.

- [x] **Step 4: Register fail-closed placeholders for session/config-heavy providers**

Keep login-required or configured providers visible in route/doctor output, but
do not pretend they are implemented:

```python
def _missing_or_unconfigured_provider(requirement: str) -> ProviderFn:
    def provider(url: str, provider_config: dict[str, Any], strategy: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(f"{requirement} is missing or not configured")
    return provider
```

This makes route readiness testable while preserving the authorization boundary.

- [x] **Step 5: Run extraction tests**

```bash
python3 -m unittest tests.test_strategy_and_extraction tests.test_platform_providers
```

Expected: PASS. YouTube, GitHub, RSS, and V2EX must produce normalized content in
unit tests. Session/config-heavy providers may fail closed with trace until a
dedicated phase implements them.

- [x] **Step 6: Commit**

```bash
git add scripts/linky/extract.py scripts/linky/providers/platforms.py tests/test_strategy_and_extraction.py tests/test_platform_providers.py
git commit -m "feat(extraction): add native platform provider slice"
```

### Phase 3: Readiness, install, docs, and verification
- **Status:** complete

### Task 4: Doctor Dependency Readiness

**Files:**
- Modify: `scripts/linky/doctor.py`
- Modify: `tests/test_source_intake_and_doctor.py`

- [x] **Step 1: Write failing doctor tests**

Add this test to `DoctorTests` in `tests/test_source_intake_and_doctor.py`:

```python
    def test_doctor_checks_dedicated_provider_requirements(self):
        strategy = {
            "fallback_chain": [{"id": "jina"}],
            "providers": {
                "youtube_ytdlp": {"requires": ["yt-dlp", "node-or-deno"]},
                "rss_feedparser": {"requires": ["feedparser"]},
                "v2ex_api": {"requires": []},
                "exa_search": {"requires": ["mcporter", "exa-mcp-config"]},
            },
        }

        report = doctor_report(
            strategy=strategy,
            module_checker=lambda name: name == "feedparser",
            command_checker=lambda name: name == "yt-dlp",
            config_checker=lambda name: False,
        )

        providers = {item["id"]: item for item in report["providers"]}
        self.assertEqual(providers["youtube_ytdlp"]["status"], "missing")
        self.assertIn("node-or-deno", providers["youtube_ytdlp"]["missing"])
        self.assertEqual(providers["rss_feedparser"]["status"], "ready")
        self.assertEqual(providers["v2ex_api"]["status"], "ready")
        self.assertIn("exa-mcp-config", providers["exa_search"]["missing"])
```

- [x] **Step 2: Run test to verify failure**

```bash
python3 -m unittest tests.test_source_intake_and_doctor.DoctorTests.test_doctor_checks_dedicated_provider_requirements
```

Expected: FAIL because `doctor_report` does not yet accept `config_checker` or scan `providers`.

- [x] **Step 3: Extend doctor requirement classification**

Modify `scripts/linky/doctor.py`:

```python
ConfigChecker = Callable[[str], bool]
COMMAND_REQUIREMENTS = {
    "playwright-cli", "yt-dlp", "gh", "bili", "twitter", "rdt", "opencli",
    "mcporter", "ffmpeg", "node", "deno", "xhs",
}
CONFIG_REQUIREMENTS = {
    "exa-mcp-config", "xiaohongshu-mcp-service", "linkedin-mcp-config",
    "xueqiu-session", "transcription-provider",
}


def doctor_report(
    strategy_path: str | Path | None = None,
    *,
    strategy: dict[str, Any] | None = None,
    module_checker: ModuleChecker | None = None,
    command_checker: CommandChecker | None = None,
    config_checker: ConfigChecker | None = None,
) -> dict[str, Any]:
    ...
    config_checker = config_checker or _config_available
    providers = []
    provider_items = list(strategy.get("fallback_chain", []))
    dedicated = strategy.get("providers", {})
    if isinstance(dedicated, dict):
        for provider_id, provider in dedicated.items():
            if isinstance(provider, dict):
                provider_items.append({"id": provider_id, **provider})

    for provider in provider_items:
        ...
        for requirement in requirements:
            if requirement == "node-or-deno":
                if not (command_checker("node") or command_checker("deno")):
                    missing.append(requirement)
            elif _is_config_requirement(requirement):
                if not config_checker(requirement):
                    missing.append(requirement)
            elif _is_command_requirement(requirement):
                if not command_checker(requirement):
                    missing.append(requirement)
            elif not module_checker(requirement):
                missing.append(requirement)
```

Add:

```python
def _is_config_requirement(requirement: str) -> bool:
    return requirement in CONFIG_REQUIREMENTS or requirement.endswith("-config") or requirement.endswith("-service")


def _config_available(name: str) -> bool:
    return False
```

- [x] **Step 4: Run doctor tests**

```bash
python3 -m unittest tests.test_source_intake_and_doctor
```

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add scripts/linky/doctor.py tests/test_source_intake_and_doctor.py
git commit -m "feat(doctor): check platform provider dependencies"
```

### Task 5: Install and Doctor Entrypoints

**Files:**
- Create: `bin/install`
- Create: `bin/linky-doctor`
- Modify: `tests/test_source_intake_and_doctor.py`

- [x] **Step 1: Write CLI smoke tests**

Add to `DoctorTests`:

```python
    def test_bin_linky_doctor_help(self):
        proc = subprocess.run(
            [str(ROOT / "bin" / "linky-doctor"), "--help"],
            check=False,
            text=True,
            capture_output=True,
        )

        self.assertEqual(proc.returncode, 0)
        self.assertIn("linky_doctor.py", proc.stdout)

    def test_bin_install_check_help(self):
        proc = subprocess.run(
            [str(ROOT / "bin" / "install"), "--help"],
            check=False,
            text=True,
            capture_output=True,
        )

        self.assertEqual(proc.returncode, 0)
        self.assertIn("Linky dependency installer", proc.stdout)
```

- [x] **Step 2: Run tests to verify failure**

Run:

```bash
python3 -m unittest tests.test_source_intake_and_doctor.DoctorTests.test_bin_linky_doctor_help tests.test_source_intake_and_doctor.DoctorTests.test_bin_install_check_help
```

Expected: FAIL because `bin/` does not exist.

- [x] **Step 3: Add `bin/linky-doctor` wrapper**

Create `bin/linky-doctor`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from linky_doctor import main


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 4: Add safe `bin/install`**

Create `bin/install`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys

COMMANDS = {
    "yt-dlp": {"auto": ["pipx", "install", "yt-dlp"], "manual": "pipx install yt-dlp"},
    "gh": {"auto": None, "manual": "Install GitHub CLI with Homebrew or the official package manager."},
    "bili": {"auto": ["pipx", "install", "bilibili-cli"], "manual": "pipx install bilibili-cli"},
    "twitter": {"auto": ["pipx", "install", "twitter-cli"], "manual": "pipx install twitter-cli"},
    "rdt": {"auto": None, "manual": "Install rdt-cli only after choosing a maintained package/source."},
    "opencli": {"auto": ["npm", "install", "-g", "@jackwener/opencli"], "manual": "npm install -g @jackwener/opencli"},
    "mcporter": {"auto": ["npm", "install", "-g", "mcporter"], "manual": "npm install -g mcporter"},
    "ffmpeg": {"auto": None, "manual": "Install ffmpeg with Homebrew or your OS package manager."},
}

MODULES = {
    "feedparser": {"auto": [sys.executable, "-m", "pip", "install", "feedparser"], "manual": "Install feedparser into Linky's Python environment."},
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Linky dependency installer")
    parser.add_argument("--check", action="store_true", help="Only report dependency status")
    parser.add_argument("--install", action="store_true", help="Install safe user-space dependencies")
    args = parser.parse_args(argv)

    if not args.check and not args.install:
        parser.print_help()
        return 0

    missing_commands = [name for name in COMMANDS if shutil.which(name) is None]
    missing_modules = [name for name in MODULES if not _module_available(name)]

    for name in missing_commands:
        action = "manual" if COMMANDS[name]["auto"] is None else "auto"
        print(f"missing command: {name} ({action})")
    for name in missing_modules:
        print(f"missing module: {name} (auto)")

    if args.check:
        return 1 if missing_commands or missing_modules else 0

    for name in missing_commands:
        command = COMMANDS[name]["auto"]
        if command is None:
            print(f"manual install required for {name}: {COMMANDS[name]['manual']}")
            continue
        subprocess.run(command, check=False)
    for name in missing_modules:
        subprocess.run(MODULES[name]["auto"], check=False)
    return 0


def _module_available(name: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(name) is not None


if __name__ == "__main__":
    raise SystemExit(main())
```

Set executable bits:

```bash
chmod +x bin/install bin/linky-doctor
```

- [x] **Step 5: Run CLI tests**

Run:

```bash
python3 -m unittest tests.test_source_intake_and_doctor
```

Expected: PASS.

- [x] **Step 6: Commit**

```bash
git add bin/install bin/linky-doctor tests/test_source_intake_and_doctor.py
git commit -m "feat(bin): add install and doctor entrypoints"
```

### Task 6: Documentation Sync

**Files:**
- Modify: `README.md`
- Modify: `docs/features/agent-reach-platforms.md`
- Modify: `docs/testing/agent-reach-platforms.md`

- [x] **Step 1: Update README provider section**

Add this paragraph under `## 采集策略` in `README.md`:

```markdown
平台型链接会优先走 Linky 原生 provider，而不是盲目进入通用网页 fallback。当前规划的 provider 包括 YouTube(`yt-dlp`)、GitHub(`gh`)、RSS(`feedparser`)、V2EX API、Bilibili(`bili-cli`)、Twitter/X(`vxTwitter` / `twitter-cli` / OpenCLI)、Reddit(OpenCLI / `rdt-cli`)、小红书(OpenCLI / `xiaohongshu-mcp` / `xhs-cli`)、LinkedIn(Jina / MCP)、雪球 API、小宇宙转录。

这些 approach 来自对 Agent Reach 的安装说明和 channel 代码研究，但 Linky 不依赖 Agent Reach runtime，不调用 `agent-reach doctor` 或 `agent-reach install`。依赖检查和安全安装由 Linky 自己的 `bin/install` 与 `bin/linky-doctor` 负责。
```

- [x] **Step 2: Update testing matrix evidence**

In `docs/testing/agent-reach-platforms.md`, keep release gates aligned with implemented test files:

```markdown
- `python3 -m unittest tests.test_strategy_and_extraction`
- `python3 -m unittest tests.test_platform_providers`
- `python3 -m unittest tests.test_source_intake_and_doctor`
- `python3 -m unittest tests.test_graph_and_report`
```

- [x] **Step 3: Run docs checks**

Run:

```bash
git diff --check
rg -n "agent-reach doctor|agent-reach install|runtime dependency" README.md docs/features/agent-reach-platforms.md docs/testing/agent-reach-platforms.md
```

Expected: `git diff --check` has no output. `rg` only shows text saying Linky does not call Agent Reach runtime commands.

- [x] **Step 4: Commit**

```bash
git add README.md docs/features/agent-reach-platforms.md docs/testing/agent-reach-platforms.md
git commit -m "docs: document native platform provider approach"
```

### Task 7: Final Verification

**Files:**
- Read: all files changed in Tasks 1 through 6

- [x] **Step 1: Run full focused test suite**

Run:

```bash
python3 -m unittest tests.test_strategy_and_extraction tests.test_platform_providers tests.test_source_intake_and_doctor tests.test_graph_and_report tests.test_gpt_safe_surface tests.test_study_mode
```

Expected: PASS.

- [x] **Step 2: Run CLI smoke checks**

Run:

```bash
bin/linky-doctor --help
bin/install --help
bin/install --check
```

Expected: help commands exit 0. `bin/install --check` may exit 1 on a machine missing optional platform tools, but it must print missing dependencies without stack traces or secrets.

- [x] **Step 3: Verify no Agent Reach runtime dependency**

Run:

```bash
rg -n "agent-reach" scripts bin references tests README.md docs | sed -n '1,120p'
```

Expected: mentions are limited to research/source documentation. Runtime code should not call `agent-reach`.

- [x] **Step 4: Commit final cleanup if needed**

If verification forced doc or test corrections:

```bash
git add README.md docs references scripts tests bin
git commit -m "chore(platforms): finalize provider integration checks"
```

## Self-Review

- Spec coverage: The plan covers native providers, domain routes, install checks, doctor checks, parser normalization, fail-closed login providers, and documentation drift.
- Placeholder scan: No missing-tool provider stub is allowed to satisfy the zero-login provider acceptance tests.
- Type consistency: Provider ids in the strategy, tests, and plan use the same snake_case names.
- Scope check: The implementation is intentionally staged. Phase 2 must ship real YouTube, GitHub, RSS, and V2EX extraction; session/config-heavy providers can be filled provider-by-provider after route, doctor, and install readiness are stable.

## GSTACK REVIEW REPORT

| Run | Status | Findings | Resolution |
|---|---|---:|---|
| CEO | clean | 1 | Native-provider direction is right; scope tightened so platform absorption means a real vertical slice, not metadata-only routing. |
| Design | skipped | 0 | No UI scope detected. |
| Eng | clean | 3 | Added phase split, real zero-login provider slice, and explicit fail-closed placeholders for session-heavy providers. |
| DX | clean | 2 | Install flow now prefers safe user-space installers and documents manual dependencies. |

VERDICT: APPROVED FOR /cf:execute

Review findings absorbed into this plan:

- **P1: Missing-tool stubs were not enough.** The original Task 3 would have registered platform ids but not implemented the YouTube/GitHub/RSS/V2EX providers that the docs and tests require. Phase 2 now requires real command/API execution with injectable runners/fetchers and normalized output.
- **P1: Install path was too brittle.** The original sample leaned on `pip install --user`, which can fail under modern managed Python installs. Task 5 now prefers `pipx` for CLI tools, npm for npm tools, and manual instructions for OS/package-manager dependencies.
- **P2: V2EX was incorrectly treated like a missing command.** V2EX has no CLI dependency and must be implemented with stdlib HTTP in the zero-login slice.
- **P2: Login-required platforms needed a clearer boundary.** The plan now keeps Reddit, XiaoHongShu, Twitter session paths, LinkedIn MCP, Xueqiu saved session, and Xiaoyuzhou transcription fail-closed unless configured.

NO UNRESOLVED DECISIONS

## Current Phase
Phase 1: Strategy, parser, and route metadata foundation
