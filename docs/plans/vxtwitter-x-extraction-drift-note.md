# Temporary Drift Note: vxTwitter / FixTweet X Extraction

## Trigger

X/Twitter URL extraction should utilize vxTwitter / FixTweet JSON endpoints before falling back to generic web extraction.

## Behavior Change

- `x.com` and `twitter.com` status URLs should prefer a dedicated third-party JSON provider.
- The provider should convert tweet JSON into Markdown while preserving provenance in metadata.
- If the third-party service fails, extraction must continue through the existing fallback chain.

## Docs And Tests To Reconcile

- Add extraction tests for the X/Twitter route and JSON-to-Markdown conversion.
- Update `references/fetch-strategy.toml` so X/Twitter routes to the dedicated provider first.
- Update `references/domain-metadata/x.com.md` to record the new preferred strategy and service limitations.

## Follow-Up

After acceptance, reconcile this note into canonical feature docs, test cases, and roadmap/status docs if this becomes a stable default.
