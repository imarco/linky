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
        lines.append(f"Author: {channel}")
    if upload_date:
        lines.append(f"Published: {upload_date}")
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
    description = str(repo.get("description") or repo.get("body") or "").strip()
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


def github_item_to_markdown(item: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    title = str(item.get("title") or item.get("name") or "GitHub item").strip()
    body = str(item.get("body") or item.get("description") or "").strip()
    url = str(item.get("url") or item.get("html_url") or "").strip()
    author = item.get("author") if isinstance(item.get("author"), dict) else {}
    user = item.get("user") if isinstance(item.get("user"), dict) else {}
    author_name = str(author.get("login") or user.get("login") or "").strip()

    lines = [f"# {title}", ""]
    if author_name:
        lines.append(f"Author: {author_name}")
    if url:
        lines.append(f"Source: [{url}]({url})")
    if body:
        lines.extend(["", body, ""])

    metadata = {
        "title": title,
        "url": url,
        "author": author_name,
        "number": item.get("number"),
        "state": item.get("state"),
    }
    return "\n".join(lines).strip() + "\n", _compact(metadata)


def feed_to_markdown(parsed: Any) -> tuple[str, dict[str, Any]]:
    feed = _value(parsed, "feed") or {}
    entries = _value(parsed, "entries") or []
    title = str(_value(feed, "title") or "RSS feed").strip()
    link = str(_value(feed, "link") or "").strip()

    lines = [f"# {title}", ""]
    if link:
        lines.append(f"Source: [{link}]({link})")
        lines.append("")
    lines.append("## Entries")
    lines.append("")
    for entry in entries[:20]:
        entry_title = str(_value(entry, "title") or "Untitled entry").strip()
        entry_link = str(_value(entry, "link") or "").strip()
        summary = str(_value(entry, "summary") or _value(entry, "description") or "").strip()
        heading = f"### [{entry_title}]({entry_link})" if entry_link else f"### {entry_title}"
        lines.extend([heading, ""])
        if summary:
            lines.extend([summary, ""])

    metadata = {"title": title, "source_url": link, "entry_count": len(entries)}
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
        result["user"] = {key: user[key] for key in ("nickname", "user_id", "nick_name") if key in user}

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


def _value(source: Any, key: str) -> Any:
    if isinstance(source, dict):
        return source.get(key)
    return getattr(source, key, None)


def _compact(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value not in (None, "", [])}
