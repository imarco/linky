"""Explicit live smoke: public fixtures, release asset and no credentials.

Not collected by pytest. Run only where direct public internet is authorized.
A previously tested W3C URL returned HTTP 403; that is recorded as a restriction,
not retried or replaced with another source for the same document.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from linky.acquire import acquire_batch, Limits


def public_source(env=None):
    env = os.environ if env is None else env
    repository = env.get('ACQUISITION_SMOKE_REPOSITORY', 'imarco/linky')
    commit = env.get('ACQUISITION_SMOKE_REF') or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9][A-Za-z0-9_.-]*', repository) or not re.fullmatch(r'[0-9a-fA-F]{40}', commit):
        raise ValueError('smoke source must be a public GitHub repository and full commit SHA')
    return repository, commit


def main():
    repository, commit = public_source()
    base = f'https://raw.githubusercontent.com/{repository}/{commit}/tests/fixtures/acquisition/'
    fixture_names = ['public.pdf', 'article.html', 'silence.wav', 'captions.vtt']
    urls = [base+name for name in fixture_names] + [
        f'https://github.com/{repository}/blob/{commit}/README.md',
        'https://github.com/yt-dlp/yt-dlp/releases/download/2026.10.26/SHA2-256SUMS',
    ]
    with tempfile.TemporaryDirectory(prefix='linky-public-smoke-') as output:
        batch = acquire_batch(urls, output, allow_media=True, article_images=True,
                              limits=Limits(max_bytes=2*1024*1024, max_total_bytes=8*1024*1024, max_files=8, max_seconds=40))
        print(json.dumps(batch.to_dict(), indent=2))
        if batch.limited or len(batch.results) != 7:
            return 1
        for result in batch.results:
            if result.status != 'complete':
                return 1
            data = (Path(output) / result.path).read_bytes()
            if hashlib.sha256(data).hexdigest() != result.sha256:
                return 1
            if result.source_url.startswith(base):
                local = ROOT/'tests/fixtures/acquisition'/result.source_url.rsplit('/',1)[-1]
                if data != local.read_bytes():
                    return 1
        return 0

if __name__ == '__main__':
    raise SystemExit(main())
