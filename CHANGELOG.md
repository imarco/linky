# Changelog

All notable changes to Linky will be documented in this file.

## [Unreleased] - 2026-11-09

### Added

- Controlled public resource acquisition CLI, safe HTTP transport, per-file provenance/hash manifests, bounded image discovery and explicit media/subtitle intent.
- Partial download accounting and verified handoff into existing source intake, without changing research/study defaults.
- Security and regression coverage for DNS/redirects, deadlines, path safety, byte limits, type mismatches and restricted responses.

### Fixed

- PR #6 GitHub host targeting, V2EX reply attribution, yt-dlp default extras, runtime/solver readiness and issue/PR coverage.
- Replaced a documentation-keyword safety test with actual credential-free HTTP and runtime API checks. Independent platform installation review remains required.

## [0.1.0.0] - 2026-05-20

### Added

- Added durable output styles so Linky can switch report voice and structure independently from where reports are delivered.
- Added the 极简白话 style for short, direct explanations of videos, articles, and other links.
- Added explanatory and learning styles inspired by Claude Code, with style instructions stored as Markdown files.
- Added user override support through `~/.config/linky/output-styles/`.
- Added tests for built-in styles, style aliases, custom style overrides, and standard report rendering compatibility.

### Changed

- Updated Linky docs, setup config, and architecture notes to describe output style selection as a first-class report assembly step.
