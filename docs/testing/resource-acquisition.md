# Controlled acquisition QA

## Baseline

Reused open PR #6 at `c4314bf142e191992d37701764b3a4493f1d9709` (base `b6d296a23bc9ce03919793a65049d2c4bfd3f445`). Remote branches and available workspace contained no later local-only commits referenced by old review comments. Baseline unittest: 68 tests, OK, one optional feedparser skip. Existing review findings were independently reproduced and corrected, not assumed already present.

## Automated verification

The initial acquisition plus PR corrections passed 148 pytest tests and 54 subtests with pytest 9.2.0/feedparser 6.0.14. `python -m compileall -q scripts bin`, CLI help commands and `git diff --check` passed. Final counts and exact published SHA should be taken from GitHub CI on the final revision.

New tests cover:

- Public IPv4/IPv6 validation, mixed public/private DNS responses, literal/ambiguous hosts, credentials in URLs, redirect denial and downgrade.
- IP pinning, no inherited proxy/auth configuration, default TLS verification/SNI, DNS timeout, headers/chunk framing watchdog and SSL handshake ownership.
- Exclusive flat output, ignored Content-Disposition, symlink rejection, private directory ownership/mode, repeated downloads, verified intake hash.
- 401/402/403/407/429/451 restrictions, HTML login disguised as PDF, type/signature mismatch, unsolicited ranges, encoded transfers, conflicting framing.
- Size/count/batch limits including discarded payloads, interrupted/truncated streams, partial hashes, no retry/alternate fetch, finite whole-request time.
- Original and redirected GitHub media intent, playlist URL/MIME rejection, actual media signatures, image-only discovery, bounded/deduplicated article assets.
- Existing research, graph/report, source intake and study tests remain included.

Independent review identified boundary failures in early revisions; each was given a failing regression before its fix. Keyword scanning of negative safety prose was replaced with behavior/API tests, not adjusted to conceal runtime capability. Host installation scanning remains a separate gate.

## Live verification and limits

The local execution environment could not resolve `raw.githubusercontent.com` or `www.w3.org`; both real CLI attempts correctly returned `error`, no artifact and no retry. This is not a live success claim. `tests/live_acquisition_smoke.py` is a separate, explicit online check in normal CI using original public PDF/PNG/WAV/VTT/article fixtures, a GitHub README and a verified public release checksum asset, with byte/hash checks. The first CI live run completed the GitHub README (6,365 bytes, SHA-256 `aaa648a8c8c6ff5ace402c00287f4e5261ecf3d48c09739cf8f8958cb8ecabf5`), but W3C returned HTTP 403. That denial is recorded without fetching the same document elsewhere; subsequent smoke uses independent original test content. It does not use secrets or browser state. Its actual outcome must be checked before declaring live acceptance.

Format verification is intentionally a MIME/signature screen and transfer accounting, not a full parser, decoder, malware scan or assertion of rights. Public direct media/subtitles are supported; platform page extraction/playlist/DRM/transcription is not. A host that requires proxy transport may reject direct DNS/socket access; Linky does not import ambient proxy credentials to compensate.

The expanded live smoke downloaded and hash-verified original PDF (599 bytes), HTML (192), WAV (204), VTT (63), PNG (69) and GitHub README. Its GitHub release redirect exposed a URL validator false positive: legitimate percent-encoded spaces in Content-Disposition query parameters were rejected. A regression now allows encoded ordinary spaces while continuing to reject raw whitespace and encoded control characters. No server access restriction was bypassed.
