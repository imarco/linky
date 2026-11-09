"""Explicit online smoke check. Not part of deterministic pytest collection.

No secrets, authentication, mirrors, executables or browser sessions are used.
Run only where direct public internet access is authorized.
"""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from linky.acquire import acquire_batch, Limits

URLS = [
    'https://github.com/imarco/linky/blob/main/README.md',
    'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
]


def main():
    with tempfile.TemporaryDirectory(prefix='linky-public-smoke-') as output:
        batch = acquire_batch(URLS, output, limits=Limits(max_bytes=2*1024*1024, max_total_bytes=4*1024*1024, max_files=2, max_seconds=40))
        print(json.dumps(batch.to_dict(), indent=2))
        for result in batch.results:
            if result.status != 'complete':
                return 1
            data = (Path(output) / result.path).read_bytes()
            if hashlib.sha256(data).hexdigest() != result.sha256:
                return 1
        return 0 if len(batch.results) == len(URLS) and not batch.limited else 1

if __name__ == '__main__':
    raise SystemExit(main())
