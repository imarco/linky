# Test Cases: Linky Source Intake Evolution

## Source Detection

1. **URL pass-through**
   - Given an `https://` URL
   - When source intake runs
   - Then it returns a `url` artifact with `success` and metadata indicating handoff to the existing URL extraction pipeline.

2. **Markdown file artifact**
   - Given a local `.md` file
   - When source intake runs
   - Then it reads text into `artifact_path_or_text`, records file metadata, and returns `success`.

3. **Text file artifact**
   - Given a local `.txt` file
   - When source intake runs
   - Then it reads text into `artifact_path_or_text`, records file metadata, and returns `success`.

4. **Unsupported extension**
   - Given a local file with an unsupported extension
   - When source intake runs
   - Then it returns `unsupported` with a trace step and error message.

5. **Missing file**
   - Given a path that does not exist
   - When source intake runs
   - Then it returns `failed` and does not throw uncaught exceptions.

6. **Batch recoverable failure**
   - Given a batch with one readable Markdown file and one PDF whose converter dependency is missing
   - When `intake_sources` runs
   - Then the batch returns both artifacts, with statuses `success` and `missing_dependency`.

## Conversion

7. **Missing markitdown**
   - Given a PDF or Office file and no `markitdown` command/module
   - When source intake runs
   - Then it returns `missing_dependency` and keeps the batch recoverable.

8. **Successful conversion**
   - Given a PDF or Office file and an injected converter
   - When source intake runs
   - Then it returns converted Markdown text with `success` and conversion trace metadata.

## Doctor

9. **Provider readiness**
   - Given strategy providers with requirements
   - When doctor runs
   - Then it reports ready/missing/disabled per provider without installing anything.

10. **Command readiness**
   - Given browser provider requires `playwright-cli`
   - When the command is missing
   - Then doctor reports `missing` and preserves the provider entry.

11. **Doctor CLI help**
    - Given `bin/linky-doctor --help`
    - When called directly
    - Then it exits successfully and prints usage text.

## Compatibility

12. **Legacy extraction remains unchanged**
    - Given `scripts/scrapling_fetch.py <url> [max_chars]`
    - When called as before
    - Then behavior remains compatible.

13. **Existing report rendering remains unchanged**
    - Given existing `ReportData` tests
    - When source intake is added
    - Then A/B/C report rendering still passes.
