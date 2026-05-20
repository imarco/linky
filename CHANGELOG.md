# Changelog

All notable changes to Linky will be documented in this file.

## [0.1.0.0] - 2026-05-20

### Added

- Added durable output styles so Linky can switch report voice and structure independently from where reports are delivered.
- Added the 极简白话 style for short, direct explanations of videos, articles, and other links.
- Added explanatory and learning styles inspired by Claude Code, with style instructions stored as Markdown files.
- Added user override support through `~/.config/linky/output-styles/`.
- Added tests for built-in styles, style aliases, custom style overrides, and standard report rendering compatibility.

### Changed

- Updated Linky docs, setup config, and architecture notes to describe output style selection as a first-class report assembly step.
