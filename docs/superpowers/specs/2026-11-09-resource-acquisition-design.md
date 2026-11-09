# Controlled resource acquisition

## Intent and approved scope

Keep Linky's research and study workflows, reuse PR #6, and add a download/archive mode for public PDFs and official course documents, GitHub files and release assets, article images, and explicitly requested public media or existing subtitles. This is a local resource collector, not an authentication or access-control workaround.

## Chosen approach

An isolated Python standard-library acquisition layer extends the existing skill. It shares source provenance with intake without changing research extraction fallback. Compared with copying download-anything's runtime, this avoids credential discovery, mirrors, cloud-drive transfers, and unbounded unpacking. Compared with shelling out to multiple downloaders, a single HTTP transport gives consistent redirect, DNS, size and status enforcement. download-anything informs routing, manifest and verification design; retain its MIT notice.

## Boundaries

- Only user-requested public HTTP(S) resources. No cookies, auth headers, netrc, browser profiles, stored credentials, shell commands or auto-installed executables in acquisition.
- Reject non-public DNS addresses before connection and pin the connection to a validated IP. Validate every redirect; forbid HTTPS downgrade. No retry or alternate source on a denial.
- Stop on authentication, payment, CAPTCHA or access-control responses. Report restricted/unsupported/partial/error rather than success.
- Stream with finite file, batch, time, redirect and count limits. No archive unpacking, execution, DRM handling or media playlists.
- Generated flat filenames under a securely opened output directory. Do not trust Content-Disposition. Use exclusive creation and reject symlinked output paths.
- Public GitHub blob URLs normalize to raw content; release-asset URLs are downloaded through the same transport. Do not use ambient gh credentials in acquisition.
- Article image discovery is opt-in and bounded. It does not recursively crawl linked pages. Media/subtitle downloads require an explicit flag; only direct publicly accessible files are supported initially.
- Per-result JSON includes source/final URL, parent source, timestamp, bytes, SHA-256, media type, status and reason. Query strings are omitted from persisted provenance. Partial files remain clearly marked and are never passed to study as complete.

## Builder decisions

Default limits: 50 MiB/file, 200 MiB/batch, 20 artifacts, five redirects, 20 seconds/socket operation and 120 seconds/file. Trusted local callers may reduce or explicitly raise size limits within CLI caps. Existing research/study extraction remains independently permission-gated. No claim that installing a skill grants permission to fetch arbitrary resources.
