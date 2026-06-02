from __future__ import annotations

import json
import re
import time
import shlex
import subprocess
import urllib.request
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote, urlparse

from .contracts import ExtractionAttempt, ExtractionResult, ExtractionTrace
from .quality import score_markdown
from .strategy import load_strategy, provider_config, quality_threshold, resolve_provider_chain

ProviderFn = Callable[[str, dict[str, Any], dict[str, Any]], dict[str, Any] | str]

_X_STATUS_DOMAINS = {"x.com", "twitter.com", "vxtwitter.com", "fxtwitter.com"}


def _http_markdown(url: str, provider: dict[str, Any], strategy: dict[str, Any]) -> str:
    max_chars = int(strategy.get("global", {}).get("max_chars", 30000))
    pattern = provider.get("url_pattern", "{url}")
    target = pattern.replace("{url}", url)
    with urllib.request.urlopen(target, timeout=int(strategy.get("global", {}).get("timeout_seconds", 15))) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    return text[:max_chars]


def _trafilatura_provider(url: str, provider: dict[str, Any], strategy: dict[str, Any]) -> dict[str, Any]:
    try:
        import trafilatura
    except ImportError as exc:
        raise RuntimeError("trafilatura 未安装。请运行: pip install trafilatura") from exc

    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise RuntimeError("trafilatura fetch_url returned empty content")
    markdown = trafilatura.extract(downloaded, output_format="markdown", include_links=True, include_images=True)
    if not markdown:
        raise RuntimeError("trafilatura extract returned empty content")
    return {"markdown": markdown, "metadata": {"provider": "trafilatura"}}


def _scrapling_provider(url: str, provider: dict[str, Any], strategy: dict[str, Any]) -> dict[str, Any]:
    from .providers.scrapling import fetch_and_extract

    markdown = fetch_and_extract(url, int(strategy.get("global", {}).get("max_chars", 30000)), strategy)
    return {"markdown": markdown, "metadata": {"provider": "scrapling"}}


def _vxtwitter_provider(url: str, provider: dict[str, Any], strategy: dict[str, Any]) -> dict[str, Any]:
    tweet_id, screen_name = _x_status_parts(url)
    pattern = str(provider.get("api_pattern", "https://api.vxtwitter.com/{screen_name}/status/{tweet_id}"))
    if "{screen_name}" in pattern and not screen_name:
        pattern = str(provider.get("id_only_api_pattern", "https://api.fxtwitter.com/status/{tweet_id}"))

    api_url = (
        pattern.replace("{tweet_id}", quote(tweet_id))
        .replace("{screen_name}", quote(screen_name or ""))
        .replace("{url}", quote(url, safe=""))
    )
    timeout = int(strategy.get("global", {}).get("timeout_seconds", 15))
    request = urllib.request.Request(
        api_url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Linky/1.0 (+https://github.com/dylanpdx/BetterTwitFix)",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("vxTwitter returned non-JSON content") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("vxTwitter returned an unexpected JSON shape")
    if _is_failed_vxtwitter_payload(payload):
        message = payload.get("message") or payload.get("error") or "vxTwitter returned an error payload"
        raise RuntimeError(str(message))

    markdown, metadata = _tweet_json_to_markdown(payload)
    return {
        "markdown": markdown,
        "metadata": {
            **metadata,
            "provider": "vxtwitter",
            "api_url": api_url,
            "tweet_id": tweet_id,
            "screen_name": screen_name,
        },
    }


def _x_status_parts(url: str) -> tuple[str, str | None]:
    parsed = urlparse(url)
    domain = parsed.netloc.lower().removeprefix("www.").removeprefix("mobile.")
    if domain not in _X_STATUS_DOMAINS and not domain.endswith(".twitter.com"):
        raise RuntimeError(f"not an X/Twitter status URL: {url}")

    parts = [part for part in parsed.path.split("/") if part]
    if "status" not in parts:
        raise RuntimeError(f"not an X/Twitter status URL: {url}")
    status_index = parts.index("status")
    if status_index + 1 >= len(parts):
        raise RuntimeError(f"missing tweet id in X/Twitter status URL: {url}")

    match = re.match(r"\d+", parts[status_index + 1])
    if not match:
        raise RuntimeError(f"invalid tweet id in X/Twitter status URL: {url}")

    screen_name = parts[status_index - 1] if status_index > 0 else None
    if screen_name in {"i", "web"}:
        screen_name = None
    return match.group(0), screen_name


def _is_failed_vxtwitter_payload(payload: dict[str, Any]) -> bool:
    code = payload.get("code")
    if isinstance(code, int) and code >= 400:
        return True
    if payload.get("tweet") is None and ("tweet" in payload or code):
        return True
    return False


def _tweet_json_to_markdown(payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    tweet = payload.get("tweet") if isinstance(payload.get("tweet"), dict) else payload
    if not isinstance(tweet, dict) or not tweet:
        raise RuntimeError("vxTwitter payload does not contain tweet data")

    author = tweet.get("author") if isinstance(tweet.get("author"), dict) else {}
    user_name = _first_text(tweet, "user_name", "author_name", "name") or _first_text(author, "name", "screen_name") or "Unknown author"
    screen_name = (_first_text(tweet, "user_screen_name", "screen_name", "handle") or _first_text(author, "screen_name", "handle") or "").lstrip("@")
    tweet_url = _first_text(tweet, "tweetURL", "tweet_url", "url") or _first_text(payload, "tweetURL", "tweet_url", "url")
    date = _first_text(tweet, "date", "created_at", "published_at")
    text = _first_text(tweet, "text", "full_text", "description") or ""
    media_urls = _media_urls(tweet)
    article = _article_payload(tweet, payload)

    metadata = {
        "tweet_url": tweet_url,
        "user_name": user_name,
        "user_screen_name": f"@{screen_name}" if screen_name else "",
        "media_count": len(media_urls),
        "content_type": "article" if article else "tweet",
    }

    if article:
        markdown = _article_to_markdown(article, tweet, user_name, screen_name, tweet_url, date, media_urls)
    else:
        markdown = _tweet_to_markdown(tweet, user_name, screen_name, tweet_url, date, text, media_urls)

    return markdown.strip() + "\n", {key: value for key, value in metadata.items() if value not in {None, ""}}


def _tweet_to_markdown(
    tweet: dict[str, Any],
    user_name: str,
    screen_name: str,
    tweet_url: str | None,
    date: str | None,
    text: str,
    media_urls: list[str],
) -> str:
    handle = f" (@{screen_name})" if screen_name else ""
    lines = [f"# {user_name}{handle}", ""]
    lines.extend(_provenance_lines(tweet_url, user_name, date))
    if text:
        lines.extend(["## Tweet", "", text.strip(), ""])
    lines.extend(_metrics_lines(tweet))
    lines.extend(_media_lines(media_urls))
    return "\n".join(lines)


def _article_to_markdown(
    article: dict[str, Any],
    tweet: dict[str, Any],
    user_name: str,
    screen_name: str,
    tweet_url: str | None,
    date: str | None,
    media_urls: list[str],
) -> str:
    title = _first_text(article, "title", "headline") or _first_text(tweet, "text") or f"{user_name} X Article"
    handle = f" (@{screen_name})" if screen_name else ""
    lines = [f"# {title.strip()}", ""]
    lines.append(f"Author: {user_name}{handle}")
    if date:
        lines.append(f"Published: {date}")
    if tweet_url:
        lines.append(f"Source: [{tweet_url}]({tweet_url})")
    lines.append("")

    body = _article_body_lines(article)
    if body:
        lines.extend(body)
        lines.append("")
    else:
        fallback = _first_text(article, "text", "body", "description") or _first_text(tweet, "text")
        if fallback:
            lines.extend([fallback.strip(), ""])

    lines.extend(_media_lines(media_urls))
    return "\n".join(lines)


def _article_payload(*sources: dict[str, Any]) -> dict[str, Any] | None:
    for source in sources:
        article = source.get("article")
        if isinstance(article, dict):
            return article
    return None


def _article_body_lines(article: dict[str, Any]) -> list[str]:
    content = article.get("content")
    blocks = content.get("blocks") if isinstance(content, dict) else article.get("blocks")
    if not isinstance(blocks, list):
        return []

    lines: list[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type", "")).lower()
        text = _block_text(block)
        if block_type in {"header", "heading", "h1", "header-one"} and text:
            lines.extend([f"# {text}", ""])
        elif block_type in {"h2", "header-two"} and text:
            lines.extend([f"## {text}", ""])
        elif block_type in {"subheader", "h3", "header-three"} and text:
            lines.extend([f"### {text}", ""])
        elif block_type in {"unordered-list-item", "ordered-list-item"} and text:
            lines.extend([f"- {text}", ""])
        elif block_type in {"list", "unordered_list", "ordered_list"}:
            items = block.get("items")
            if isinstance(items, list):
                for item in items:
                    item_text = _block_text(item) if isinstance(item, dict) else str(item).strip()
                    if item_text:
                        lines.append(f"- {item_text}")
                lines.append("")
            elif text:
                lines.extend([text, ""])
        elif block_type in {"quote", "blockquote"} and text:
            lines.extend([f"> {line}" for line in text.splitlines() if line.strip()])
            lines.append("")
        elif text:
            lines.extend([text, ""])
    return lines


def _block_text(block: dict[str, Any]) -> str:
    for key in ("text", "plain_text", "content", "body"):
        value = block.get(key)
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, dict):
            nested = _block_text(value)
            if nested:
                return nested
    return ""


def _first_text(source: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = source.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _media_urls(tweet: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    for key in ("mediaURLs", "media_urls", "mediaURLs_extended"):
        value = tweet.get(key)
        if isinstance(value, list):
            urls.extend(str(item) for item in value if isinstance(item, str) and item.startswith("http"))
    media_extended = tweet.get("media_extended")
    if isinstance(media_extended, list):
        for item in media_extended:
            if not isinstance(item, dict):
                continue
            url = _first_text(item, "url", "thumbnail_url", "image_url")
            if url and url.startswith("http"):
                urls.append(url)
    return list(dict.fromkeys(urls))


def _provenance_lines(tweet_url: str | None, user_name: str, date: str | None) -> list[str]:
    lines = [f"Author: {user_name}"]
    if date:
        lines.append(f"Published: {date}")
    if tweet_url:
        lines.append(f"Source: [{tweet_url}]({tweet_url})")
    lines.append("")
    return lines


def _metrics_lines(tweet: dict[str, Any]) -> list[str]:
    metrics = []
    for label, key in (("Likes", "likes"), ("Retweets", "retweets"), ("Replies", "replies")):
        value = tweet.get(key)
        if isinstance(value, int):
            metrics.append(f"- {label}: {value}")
    if not metrics:
        return []
    return ["## Metrics", "", *metrics, ""]


def _media_lines(media_urls: list[str]) -> list[str]:
    if not media_urls:
        return []
    lines = ["## Media", ""]
    for index, media_url in enumerate(media_urls, start=1):
        lines.append(f"![media {index}]({media_url})")
    lines.append("")
    return lines


def _command_provider(url: str, provider: dict[str, Any], strategy: dict[str, Any]) -> dict[str, Any]:
    command = provider.get("command")
    if not command:
        raise RuntimeError(f"provider {provider.get('id', 'unknown')} has no command")

    max_chars = int(strategy.get("global", {}).get("max_chars", 30000))
    skill_dir = Path(__file__).resolve().parents[2]
    rendered = (
        command.replace("{url}", shlex.quote(url))
        .replace("{max_chars}", str(max_chars))
        .replace("{skill_dir}", shlex.quote(str(skill_dir)))
    )
    proc = subprocess.run(
        rendered,
        shell=True,
        check=False,
        text=True,
        capture_output=True,
        timeout=int(strategy.get("global", {}).get("timeout_seconds", 15)),
    )
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or f"command exited {proc.returncode}"
        raise RuntimeError(message)
    return {"markdown": proc.stdout[:max_chars], "metadata": {"command": rendered}}


BUILTIN_PROVIDERS: dict[str, ProviderFn] = {
    "jina": lambda url, provider, strategy: {"markdown": _http_markdown(url, provider, strategy), "metadata": {}},
    "webfetch": lambda url, provider, strategy: {"markdown": _http_markdown(url, provider, strategy), "metadata": {}},
    "vxtwitter": _vxtwitter_provider,
    "trafilatura": _trafilatura_provider,
    "scrapling": _scrapling_provider,
    "browser": _command_provider,
}


def extract_url(
    url: str,
    strategy_path: str | Path | None = None,
    strategy: dict[str, Any] | None = None,
    providers: dict[str, ProviderFn] | None = None,
) -> ExtractionResult:
    if strategy is None:
        if strategy_path is None:
            strategy_path = Path(__file__).resolve().parents[2] / "references" / "fetch-strategy.toml"
        strategy = load_strategy(strategy_path)

    provider_fns = dict(BUILTIN_PROVIDERS)
    if providers:
        provider_fns.update(providers)

    trace = ExtractionTrace(url=url)
    threshold = quality_threshold(strategy)
    errors: list[str] = []
    best_markdown = ""
    best_provider: str | None = None
    best_quality = {"score": 0.0, "status": "failed", "reasons": ["not_attempted"]}
    best_metadata: dict[str, Any] = {}

    for provider_id in resolve_provider_chain(url, strategy):
        provider = provider_config(strategy, provider_id)
        fn = provider_fns.get(provider_id)
        start = time.monotonic()
        if not fn:
            message = f"provider not implemented: {provider_id}"
            errors.append(message)
            trace.attempts.append(
                ExtractionAttempt(provider=provider_id, status="failed", elapsed_ms=0, error=message)
            )
            continue

        try:
            raw = fn(url, provider, strategy)
            if isinstance(raw, str):
                markdown = raw
                metadata: dict[str, Any] = {}
            else:
                markdown = str(raw.get("markdown", ""))
                metadata = dict(raw.get("metadata", {}))

            quality = score_markdown(markdown)
            elapsed_ms = int((time.monotonic() - start) * 1000)
            fallback_reason = None if quality["score"] >= threshold else "low_quality"
            trace.attempts.append(
                ExtractionAttempt(
                    provider=provider_id,
                    status=quality["status"],
                    elapsed_ms=elapsed_ms,
                    content_length=len(markdown),
                    fallback_reason=fallback_reason,
                )
            )

            if quality["score"] > float(best_quality.get("score", 0.0)):
                best_markdown = markdown
                best_provider = provider_id
                best_quality = quality
                best_metadata = metadata

            if quality["score"] >= threshold and quality["status"] == "success":
                trace.finish(provider_id, "success", quality["score"])
                return ExtractionResult(
                    url=url,
                    status="success",
                    provider=provider_id,
                    markdown=markdown,
                    metadata=metadata,
                    quality=quality,
                    trace=trace,
                    errors=errors,
                )
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            message = str(exc)
            errors.append(f"{provider_id}: {message}")
            trace.attempts.append(
                ExtractionAttempt(provider=provider_id, status="failed", elapsed_ms=elapsed_ms, error=message)
            )

    final_status = str(best_quality.get("status", "failed"))
    if best_markdown and final_status == "success":
        final_status = "partial"
    trace.finish(best_provider, final_status, float(best_quality.get("score", 0.0)))
    return ExtractionResult(
        url=url,
        status=final_status,
        provider=best_provider,
        markdown=best_markdown,
        metadata=best_metadata,
        quality=best_quality,
        trace=trace,
        errors=errors,
    )
