"""Bounded, credential-free public resource acquisition, separate from research.

Downloaded archives and programs are never extracted or executed. Results are
immutable manifests; partial files are never advertised as complete artifacts.
"""
from __future__ import annotations

import hashlib
import http.client
import json
import os
import re
import stat
import time
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field, replace
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

from .contracts import utc_now_iso
from .safe_http import RestrictedURL, SafeHTTPClient, public_url, validate_url

DOCUMENTS = {'.pdf', '.ppt', '.pptx', '.doc', '.docx', '.xls', '.xlsx', '.odt', '.odp'}
IMAGES = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif'}
MEDIA = {'.mp4', '.m4a', '.mp3', '.webm', '.ogg', '.wav', '.mov', '.flac'}
SUBTITLES = {'.vtt', '.srt', '.json3'}
PLAYLISTS = {'.m3u', '.m3u8', '.mpd'}
PLAYLIST_MIMES = {'application/vnd.apple.mpegurl', 'application/x-mpegurl', 'audio/mpegurl', 'audio/x-mpegurl', 'application/mpegurl', 'application/dash+xml'}


@dataclass(frozen=True)
class Limits:
    max_bytes: int = 50 * 1024 * 1024
    max_total_bytes: int = 200 * 1024 * 1024
    max_files: int = 20
    timeout: float = 20
    max_seconds: float = 120
    max_redirects: int = 5

    def __post_init__(self):
        if not (0 < self.max_bytes <= 1024**3 and 0 < self.max_total_bytes <= 5*1024**3 and 1 <= self.max_files <= 100 and 0 < self.timeout <= 60 and 0 < self.max_seconds <= 600 and 0 <= self.max_redirects <= 10):
            raise ValueError('limits must be positive and within supported caps')


@dataclass
class AcquisitionResult:
    source_url: str
    status: str = 'error'
    kind: str = 'unknown'
    final_url: str | None = None
    parent_url: str | None = None
    path: str | None = None
    manifest_path: str | None = None
    size_bytes: int = 0
    transferred_bytes: int = 0
    schema_version: int = 1
    sha256: str | None = None
    content_type: str | None = None
    partial: bool = False
    reason: str | None = None
    redirects: list[str] = field(default_factory=list)
    fetched_at: str = field(default_factory=utc_now_iso)
    provider: str = 'public_http'

    def to_dict(self):
        return asdict(self)


@dataclass
class AcquisitionBatch:
    results: list[AcquisitionResult]
    limited: bool = False
    reason: str | None = None

    def to_dict(self):
        return {'results': [r.to_dict() for r in self.results], 'limited': self.limited, 'reason': self.reason}


class ArchiveDirectory:
    """Walk/create the destination without following symlink components."""
    def __init__(self, directory):
        self.path = Path(os.path.abspath(directory))
        fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
        try:
            for part in self.path.parts[1:]:
                try:
                    os.mkdir(part, mode=0o700, dir_fd=fd)
                except FileExistsError:
                    pass
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = next_fd
        except OSError as exc:
            os.close(fd)
            raise ValueError('output directory must be writable and contain no symlinks') from exc
        info = os.fstat(fd)
        if info.st_uid != os.getuid() or info.st_mode & 0o022:
            os.close(fd)
            raise ValueError('output directory must be owned by this user and not group/world-writable')
        self.fd = fd

    def create(self, name):
        if Path(name).name != name or name in {'.', '..'}:
            raise ValueError('invalid archive filename')
        return os.fdopen(os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=self.fd), 'wb')

    def read(self, name, limit):
        if Path(name).name != name:
            raise ValueError("invalid archive filename")
        with os.fdopen(os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=self.fd), "rb") as source:
            return source.read(limit)

    def remove(self, name):
        os.unlink(name, dir_fd=self.fd)

    def complete(self, source, target):
        # Hard-link creation fails if the target exists, unlike rename/replace.
        os.link(source, target, src_dir_fd=self.fd, dst_dir_fd=self.fd, follow_symlinks=False)
        self.remove(source)

    def close(self):
        os.close(self.fd)


def _route(url):
    p = validate_url(url)
    suffix = Path(unquote(p.path)).suffix.lower()
    if suffix in PLAYLISTS:
        return url, 'unsupported', suffix
    host = p.hostname.lower()
    parts = p.path.strip('/').split('/')
    if host in {'github.com', 'www.github.com'}:
        if len(parts) >= 5 and parts[2] == 'blob':
            if any(part in {'', '.', '..'} for part in parts) or any('/' in unquote(part) or '\\' in unquote(part) for part in parts):
                raise RestrictedURL('ambiguous GitHub file path')
            # A URL using a branch name containing slashes must use a raw URL
            # or immutable commit URL; no ambient gh authentication is consulted.
            return urlunsplit(('https', 'raw.githubusercontent.com', '/'+'/'.join(parts[:2]+parts[3:]), '', '')), 'github_file', suffix
        if len(parts) >= 6 and parts[2:4] == ['releases', 'download']:
            return url, 'github_file', suffix
        return url, 'unsupported', suffix
    if host == 'raw.githubusercontent.com' or host == 'release-assets.githubusercontent.com':
        return url, 'github_file', suffix
    if host in {'youtube.com', 'www.youtube.com', 'youtu.be', 'vimeo.com', 'www.bilibili.com', 'bilibili.com'} or suffix in PLAYLISTS:
        return url, 'unsupported', suffix
    if suffix in MEDIA:
        return url, 'media', suffix
    if suffix in SUBTITLES:
        return url, 'subtitle', suffix
    if suffix in DOCUMENTS:
        return url, 'document', suffix
    if suffix in IMAGES:
        return url, 'image', suffix
    return url, 'web', suffix


def _sniff_kind(kind, content_type):
    if content_type.startswith(('audio/', 'video/')):
        return 'media'
    if content_type in {'text/vtt', 'application/x-subrip'}:
        return 'subtitle'
    if content_type == 'application/pdf':
        return 'document'
    if content_type.startswith('image/'):
        return 'image'
    return kind


def _is_image(prefix):
    return (prefix.startswith((b'\x89PNG\r\n\x1a\n', b'\xff\xd8\xff', b'GIF87a', b'GIF89a'))
            or prefix[:4] == b'RIFF' and prefix[8:12] == b'WEBP'
            or prefix[4:8] == b'ftyp' and b'avif' in prefix[:32])


def _validate_body(prefix, kind, suffix, content_type):
    text = prefix.lstrip(b'\xef\xbb\xbf\x00\t\r\n ').lower()
    html = text.startswith((b'<!doctype html', b'<html', b'<form')) or content_type == 'text/html'
    if html and (b'captcha' in text or b'cf-chl-' in text or b'access denied' in text or b'payment required' in text or (b'<form' in text and any(x in text for x in (b'sign in', b'log in', b'login', b'password')))):
        return 'restricted', 'access-control page received; no alternate retrieval attempted'
    if html and kind != 'web':
        return 'unsupported', 'HTML returned instead of the requested file'
    if kind == 'image':
        if not _is_image(prefix):
            return 'unsupported', 'unsupported or invalid image (SVG is not archived as an image)'
    elif suffix == '.pdf' or content_type == 'application/pdf':
        if not prefix.startswith(b'%PDF-'):
            return 'unsupported', 'response is not a PDF'
    elif kind == 'document' and suffix in {'.docx', '.pptx', '.xlsx', '.odt', '.odp'} and not prefix.startswith(b'PK\x03\x04'):
        return 'unsupported', 'response is not an Office/OpenDocument container'
    elif kind == 'document' and suffix in {'.doc', '.ppt', '.xls'} and not prefix.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
        return 'unsupported', 'response is not a legacy Office container'
    elif kind == 'media' or suffix in MEDIA:
        if not (prefix[4:8] == b'ftyp' or prefix.startswith((b'ID3', b'OggS', b'fLaC', b'\x1aE\xdf\xa3')) or prefix[:4] == b'RIFF' and prefix[8:12] == b'WAVE' or len(prefix) > 1 and prefix[0] == 255 and prefix[1] & 224 == 224):
            return 'unsupported', 'response does not have a recognized media signature'
    elif kind == 'subtitle' or suffix in SUBTITLES:
        if suffix == '.json3':
            if not text.startswith(b'{'):
                return 'unsupported', 'response is not JSON caption data'
        elif not (text.startswith(b'webvtt') or b'-->' in prefix):
            return 'unsupported', 'response is not recognized subtitle text'
    elif kind == 'web' and not (html or content_type.startswith('text/') or content_type in {'application/json', 'application/xml'}):
        return 'unsupported', 'unrecognized resource type; use a public direct document/file URL'
    return None


def acquire(url: str, output_dir, *, allow_media=False, limits=None, parent_url=None, expected_kind=None):
    limits = limits or Limits()
    archive = ArchiveDirectory(output_dir)
    token = uuid.uuid4().hex
    result = AcquisitionResult(source_url=public_url(url), parent_url=public_url(parent_url) if parent_url else None)
    response = None
    partial_name = f'{token}.partial'
    created = False
    prefix = b''
    digest = hashlib.sha256()
    try:
        try:
            target, result.kind, suffix = _route(url)
            if result.kind == 'unsupported':
                result.status, result.reason = 'unsupported', 'provide a direct public file URL; platform extraction and playlists are not supported in acquisition'
            elif (result.kind in {'media', 'subtitle'} or suffix in MEDIA | SUBTITLES) and not allow_media:
                result.status, result.reason = 'needs_intent', 'public media/subtitles require an explicit user request (--allow-media)'
            else:
                response = SafeHTTPClient(timeout=limits.timeout, max_redirects=limits.max_redirects, max_seconds=limits.max_seconds).open(target)
                _, final_kind, final_suffix = _route(response.url)
                result.final_url = public_url(response.url)
                result.redirects = response.redirects
                result.content_type = response.getheader('Content-Type', '').split(';')[0].strip().lower()[:120]
                result.kind = _sniff_kind(result.kind, result.content_type)
                length = response.getheader('Content-Length')
                expected = int(length) if length and length.isdecimal() else None
                if response.getheader('Transfer-Encoding') and length is not None:
                    result.status, result.reason = 'unsupported', 'conflicting transfer framing headers'
                elif response.getheader('Transfer-Encoding', '').lower() not in {'', 'chunked'}:
                    result.status, result.reason = 'unsupported', 'unsupported transfer framing'
                elif result.content_type in PLAYLIST_MIMES:
                    result.status, result.reason = 'unsupported', 'media playlists and manifests are not supported'
                elif final_kind == 'unsupported':
                    result.status, result.reason = 'unsupported', 'redirect target is not a supported public resource'
                elif final_suffix in MEDIA | SUBTITLES and not allow_media:
                    result.status, result.reason = 'needs_intent', 'redirected media/subtitles require explicit user intent'
                elif expected_kind == 'image' and result.kind != 'image':
                    result.status, result.reason = 'unsupported', 'article image reference did not return an image'
                elif response.status in {401, 402, 403, 407, 429, 451}:
                    result.status, result.reason = 'restricted', f'HTTP {response.status}; stopped without retry'
                elif response.status == 206:
                    result.status, result.reason = 'unsupported', 'unsolicited partial HTTP response'
                elif response.status != 200:
                    result.status, result.reason = 'error', f'HTTP {response.status}'
                elif response.getheader('Content-Encoding', 'identity').lower() not in {'identity', ''}:
                    result.status, result.reason = 'unsupported', 'compressed HTTP transfer not accepted'
                elif (result.kind in {'media', 'subtitle'} or suffix in MEDIA | SUBTITLES) and not allow_media:
                    result.status, result.reason = 'needs_intent', 'media/subtitles require explicit user intent'
                elif expected is not None and expected > limits.max_bytes:
                    result.status, result.reason = 'too_large', 'declared size exceeds per-file limit'
                else:
                    deadline = time.monotonic() + limits.max_seconds
                    with archive.create(partial_name) as output:
                        created = True
                        while True:
                            if time.monotonic() >= deadline:
                                result.reason = 'transfer time limit reached'
                                break
                            chunk = response.read(min(64*1024, limits.max_bytes - result.size_bytes))
                            if not chunk:
                                result.status = 'complete'
                                break
                            result.transferred_bytes += len(chunk)
                            allowed = chunk[:limits.max_bytes - result.size_bytes]
                            output.write(allowed)
                            digest.update(allowed)
                            result.size_bytes += len(allowed)
                            prefix = (prefix + allowed)[:16384]
                            if result.size_bytes >= limits.max_bytes:
                                if expected == result.size_bytes:
                                    result.status = 'complete'
                                else:
                                    result.reason = 'stream reached per-file or remaining batch limit'
                                break
                        output.flush()
                    if result.size_bytes and result.status != 'complete':
                        result.status = 'partial'
                    if expected is not None and result.size_bytes != expected and result.status == 'complete':
                        result.status, result.reason = 'partial', 'received size differs from Content-Length'
                    if not result.size_bytes:
                        result.status, result.reason = 'error', 'empty response'
                    invalid = _validate_body(prefix, expected_kind or result.kind, suffix or final_suffix, result.content_type)
                    if invalid:
                        result.status, result.reason = invalid
        except RestrictedURL as exc:
            result.status, result.reason = 'restricted', str(exc)
        except (OSError, ValueError, http.client.HTTPException) as exc:
            # Never persist raw exception text: it may contain signed URL tokens.
            result.status = 'partial' if result.size_bytes else 'error'
            result.reason = f'transfer failed ({type(exc).__name__}); no retry attempted'
        if created:
            if result.status in {'complete', 'partial'} and result.size_bytes:
                result.sha256 = digest.hexdigest()
                result.partial = result.status == 'partial'
                if result.partial:
                    result.path = partial_name
                else:
                    ext = suffix if re.fullmatch(r'\.[a-zA-Z0-9]{1,10}', suffix or '') else '.bin'
                    if result.kind == 'web':
                        ext = '.html.txt' if result.content_type == 'text/html' else '.txt'
                    name = f'{token}{ext}'
                    archive.complete(partial_name, name)
                    result.path = name
            else:
                archive.remove(partial_name)
                result.size_bytes = 0
        result.manifest_path = f'{token}.json'
        with archive.create(result.manifest_path) as manifest:
            manifest.write((json.dumps(result.to_dict(), ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
        return result
    finally:
        if response is not None:
            response.close()
        archive.close()


class _Images(HTMLParser):
    def __init__(self, base, limit):
        super().__init__()
        self.base, self.limit, self.urls, self.overflow = base, limit, [], False
        self.seen = set()

    def handle_starttag(self, tag, attrs):
        if tag != 'img':
            return
        attrs = dict(attrs)
        source = attrs.get('src') or attrs.get('data-src')
        if not source:
            return
        url = urljoin(self.base, source)
        if url in self.seen:
            return
        self.seen.add(url)
        if len(self.urls) >= self.limit:
            self.overflow = True
        else:
            self.urls.append(url)


def acquire_batch(urls, output_dir, *, allow_media=False, article_images=False, limits=None):
    limits = limits or Limits()
    queue = deque((url, None) for url in dict.fromkeys(urls))
    seen = set(urls)
    batch = AcquisitionBatch([])
    total = 0
    while queue:
        if len(batch.results) >= limits.max_files or total >= limits.max_total_bytes:
            batch.limited, batch.reason = True, 'batch count or byte limit reached; remaining resources not requested'
            break
        url, parent = queue.popleft()
        per_file = replace(limits, max_bytes=min(limits.max_bytes, limits.max_total_bytes - total))
        result = acquire(url, output_dir, allow_media=allow_media, limits=per_file, parent_url=parent, expected_kind='image' if parent else None)
        batch.results.append(result)
        total += result.transferred_bytes
        if article_images and parent is None and result.status == 'complete' and result.kind == 'web' and result.content_type == 'text/html':
            # Bound parser input separately from the document download budget.
            archive = ArchiveDirectory(output_dir)
            try:
                raw = archive.read(result.path, 2*1024*1024 + 1)
            except OSError:
                batch.limited, batch.reason = True, 'archived article changed before image discovery'
                continue
            finally:
                archive.close()
            if len(raw) != result.size_bytes or hashlib.sha256(raw).hexdigest() != result.sha256:
                batch.limited, batch.reason = True, 'article hash changed or image-discovery parse limit exceeded'
                continue
            if len(raw) > 2*1024*1024:
                batch.limited, batch.reason = True, 'article exceeds image-discovery parse limit'
                continue
            parser = _Images(result.final_url or url, limits.max_files)
            parser.feed(raw.decode('utf-8', errors='replace'))
            if parser.overflow:
                batch.limited, batch.reason = True, 'article image discovery limit reached'
            for image_url in parser.urls:
                if image_url not in seen:
                    queue.append((image_url, result.source_url))
                    seen.add(image_url)
    return batch


def to_source_artifact(result: AcquisitionResult, output_dir):
    """Explicit handoff to existing intake; incomplete resources never qualify."""
    from .intake import SourceArtifact, detect_source_kind
    if result.status != 'complete' or not result.path or not result.sha256:
        raise ValueError('only complete, hashed acquisitions may enter source intake')
    archive = ArchiveDirectory(output_dir)
    try:
        data = archive.read(result.path, result.size_bytes + 1)
        if len(data) != result.size_bytes or hashlib.sha256(data).hexdigest() != result.sha256:
            raise ValueError('archived artifact changed; acquire it again before intake')
        path = str(archive.path / result.path)
    finally:
        archive.close()
    return SourceArtifact(id=result.sha256[:16], kind=detect_source_kind(path), original_uri=result.source_url,
                          artifact_path_or_text=path, status='success', metadata={
                              'sha256': result.sha256, 'size_bytes': result.size_bytes,
                              'final_url': result.final_url, 'fetched_at': result.fetched_at,
                              'acquisition_manifest': result.manifest_path, 'extraction_pipeline': 'local_file_intake',
                          })
