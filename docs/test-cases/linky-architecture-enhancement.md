# Test Cases: Linky Architecture Enhancement

## Extraction Strategy

1. **Load fallback chain from TOML**
   - Given a strategy file with providers and fallback order
   - When the strategy loader runs
   - Then it returns the ordered provider list and requirements without hard-coded defaults overriding the file.

2. **Domain route override**
   - Given a URL matching `mp.weixin.qq.com`
   - When a domain route says `go_to = "scrapling"` and skips `jina`
   - Then extraction starts at `scrapling` and records the skipped providers in trace.

3. **Quality-driven fallback**
   - Given a provider returns success but short/noisy content below threshold
   - When quality scoring runs
   - Then the next provider is attempted and trace records `low_quality` as fallback reason.

4. **Unavailable optional dependency**
   - Given `trafilatura` or `scrapling` is not installed
   - When the provider is selected
   - Then extraction skips that provider with a clear trace error and continues fallback.

## Compatibility

5. **Legacy Scrapling CLI still works**
   - Given `scripts/scrapling_fetch.py <url> [max_chars]`
   - When called directly
   - Then it prints Markdown to stdout and exits non-zero on dependency or extraction failure.

6. **Existing Skill usage remains unchanged**
   - Given a user provides URLs in natural language
   - When Linky runs through the Skill
   - Then it still produces the A/B/C report with typed analysis cards.

## Research Loop

7. **Autoresearch gap detection**
   - Given a GitHub repo page with no docs/pricing/homepage context
   - When the research loop critiques the analysis
   - Then it records missing context and either schedules optional補采 or marks the gap in `ReportData`.

8. **No infinite expansion**
   - Given optional補采 discovers related links
   - When the configured depth or link budget is reached
   - Then it stops and records the budget limit in trace.

## Research Graph

9. **Node and edge de-duplication**
   - Given multiple documents mention the same topic/entity
   - When graph construction runs
   - Then duplicate nodes merge by stable id and edges remain typed.

10. **Graph output is optional**
    - Given graph output is disabled in strategy/config
    - When a report is generated
    - Then report generation still works without graph files.

## Report Assembly

11. **Structured data renders Markdown**
    - Given `ReportData` with multiple typed items
    - When Markdown rendering runs
    - Then the output includes A. research overview, B. typed entries, and C. conclusions.

12. **Output style can render minimal plain language**
    - Given `ReportData` with `output_style = "极简白话"`
    - When Markdown rendering runs
    - Then the output uses the five fixed sections: conclusion, what it said, key points, usefulness, and original link.

13. **Output style definitions can be loaded**
    - Given the built-in `explanatory` and `learning` styles
    - When Linky resolves output style instructions
    - Then both styles expose prompt instructions and keep the standard renderer.

14. **Blocked links remain visible**
    - Given a URL fails due to login wall
    - When the final report is assembled
    - Then the URL appears with blocked status, trace summary, and limited-analysis warning.
