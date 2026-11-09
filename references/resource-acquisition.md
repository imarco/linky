# Public resource acquisition

## When and how

Use this mode when the user asks to download, save or archive identified public resources. Research and study remain the existing workflows; do not download media just because a research page mentions it. First establish the requested URLs, destination and whether article images or public media/subtitles are in scope. A request to download the given URLs covers the public files, but not login, payment, terms acceptance, credentials, private material or file sharing elsewhere.

Run `python3 bin/linky-get URL... --output DESTINATION` from the installed Linky directory. Python 3.11+ on Linux/macOS is sufficient; there are no downloader dependencies. Relative paths are relative to that working directory. When space is tight, choose lower limits before fetching.

- `--article-images`: fetch image URLs in the supplied article's `img src` or `data-src` attributes, once each. No recursive crawling, CSS image extraction, `srcset` selection or linked-page discovery. Discovered responses must have an image MIME type and supported signature.
- `--allow-media`: use only for an explicit user request for public direct media or existing subtitle files. It does not authorize access-controlled content, playlists, DRM handling, ASR/transcription, browser-session access or platform downloads.
- `--max-bytes`, `--max-total-bytes`, `--max-files`: defaults are 50 MiB, 200 MiB and 20 files. Hard caps are 1 GiB/file, 5 GiB/batch and 100 results.

## Supported resources

- Public PDFs and official PPT/PPTX/DOC/DOCX/XLS/XLSX/ODT/ODP course documents.
- GitHub `blob` file URLs (normalized to raw), raw file URLs, and explicit release asset URLs ending in `/releases/download/TAG/FILE`. A release page is not an asset. Prefer immutable commit URLs; slash-containing branches should use a verified raw URL.
- PNG/JPEG/GIF/WebP/AVIF images. SVG is not accepted as an image.
- Explicitly requested direct MP4/M4A/MP3/WebM/OGG/WAV/MOV/FLAC files and existing VTT/SRT/JSON3 subtitles. No YouTube/Bilibili page-to-media extractor in this mode. Existing research caption extraction is separate.
- Public article HTML and text are archived as text, not opened or executed.

## Safety and limits

The downloader sends only fixed public GET headers, never cookies, auth headers, `.netrc`, browser profiles, gh configuration or proxy environment. Public DNS answers are all checked and the socket connects to the checked IP. Every redirect is checked; HTTPS downgrade, local/private/metadata addresses, ambiguous hosts, userinfo and nonstandard ports are rejected. There are at most five redirects, 20 seconds per socket operation and a 120-second whole-request deadline (including DNS/redirects/headers/body). Resolver work is concurrency-bounded and cannot start a connection after timeout.

Authentication/payment/rate-limit/legal restriction responses and recognized access-control HTML stop that resource. No retry, account switching, external fallback or alternative source is attempted. Obfuscated challenges may be classified unsupported rather than identified precisely; the downloader does not solve them.

Output directories must be owned by the current user, not group/world-writable, and contain no symlink path components. Filenames are generated, exclusive and flat. Content-Disposition is ignored. Archives/executables remain opaque files with non-executable permissions; nothing is extracted or run. MIME/signature checks catch obvious mismatches but are not malware scanning or full-format validation. Only archive resources you trust and are entitled to use.

## Results and downstream study

Each result has its own JSON manifest with schema version, original/final URL, parent article, redirect trail, timestamp, provider, type, status, byte count and SHA-256. URL query strings, fragments and userinfo are omitted from persisted provenance. A hash checks local content integrity, not publisher authenticity or licensing. `transferred_bytes` counts received payload even if invalid content is discarded, so batch budgets do not reset on rejected files.

- `complete`: a finished transfer with supported content/signature. File and SHA-256 are available.
- `partial`: interrupted, truncated or limit-stopped transfer. Retained bytes use `.partial`, with their own size/hash. Do not present them as usable completed resources.
- `restricted`: public-resource boundary or server restriction. Stop and tell the user what input/action is needed.
- `needs_intent`: media/subtitles were not explicitly requested. Ask only if the user actually wants them.
- `unsupported`, `too_large`, `error`: explain the specific reason; do not claim completion.

CLI prints the complete batch report and returns 0 only when all requested resources complete with no truncation of the batch. Exit 1 means incomplete results; exit 2 means invalid options or output failure. Review every result, including `limited`, before summarizing success. A batch limit means remaining resources were not fetched; ask before raising scope or limits.

For an explicitly requested download-and-study task, `linky.acquire.to_source_artifact(result, destination)` accepts only complete results and verifies the local hash before returning an intake artifact. Feed that local file to the existing intake/study workflow; conversion remains an optional dependency. Preserve original URL and acquisition manifest in the study output. Never feed partial or restricted downloads into analysis as if they were complete.

## Installation

Repository availability and a passing test suite are not skill installation approval. Use the host's supported skill installation/review path. If the platform rejects installation, stop, retain the code and explain the blocker. Do not rename, omit code, or weaken checks to obtain installation. This skill does not install or invoke download-anything's original skill.
