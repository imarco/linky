import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from linky import acquire
from test_safe_http import FakeResponse

PDF = b'%PDF-1.4\n' + b'x' * 100 + b'\n%%EOF\n'

class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()
    def run_get(self, body=PDF, headers=None, url='https://example.com/lecture.pdf', **kwargs):
        response = FakeResponse(body=body, headers=headers or {'Content-Type': 'application/pdf'})
        with patch('linky.safe_http.SafeHTTPClient.open', return_value=response):
            result = acquire.acquire(url, self.root, **kwargs)
        self.assertTrue(response.closed)
        return result

    def test_public_pdf_has_provenance_hash_and_manifest(self):
        result = self.run_get(url='https://example.com/lecture.pdf?token=secret')
        self.assertEqual(result.status, 'complete')
        self.assertEqual(result.sha256, hashlib.sha256(PDF).hexdigest())
        self.assertEqual(result.size_bytes, len(PDF))
        self.assertEqual((self.root / result.path).read_bytes(), PDF)
        manifest = json.loads((self.root / result.manifest_path).read_text())
        self.assertEqual(manifest['source_url'], 'https://example.com/lecture.pdf')
        self.assertNotIn('secret', json.dumps(manifest))
        self.assertFalse(result.partial)

    def test_path_is_generated_and_content_disposition_not_trusted(self):
        result = self.run_get(headers={'Content-Type': 'application/pdf', 'Content-Disposition': 'attachment; filename="../../evil.py"'})
        self.assertEqual(result.status, 'complete')
        self.assertEqual(Path(result.path).parent, Path('.'))
        self.assertNotEqual(result.path, 'evil.py')

    def test_same_filename_twice_never_overwrites(self):
        first, second = self.run_get(), self.run_get()
        self.assertNotEqual(first.path, second.path)
        self.assertTrue((self.root / first.path).exists())

    def test_symlink_output_is_rejected(self):
        outside = self.root / 'outside'; outside.mkdir()
        target = self.root / 'link'; target.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError), patch('linky.safe_http.SafeHTTPClient.open') as request:
            acquire.acquire('https://example.com/a.pdf', target)
        request.assert_not_called()
        self.assertFalse(list(outside.iterdir()))

    def test_unsafe_url_is_restricted_without_network(self):
        with patch('linky.safe_http.SafeHTTPClient.open') as request:
            result = acquire.acquire('http://127.0.0.1/a.pdf', self.root)
        self.assertEqual(result.status, 'restricted')
        self.assertIsNone(result.path)
        request.assert_not_called()

    def test_denial_never_falls_back_or_retries(self):
        for status in [401, 402, 403, 407, 429, 451]:
            with self.subTest(status=status), patch('linky.safe_http.SafeHTTPClient.open', return_value=FakeResponse(status=status)) as request:
                result = acquire.acquire('https://example.com/a.pdf', self.root)
                self.assertEqual(result.status, 'restricted')
                self.assertIsNone(result.path)
                self.assertEqual(request.call_count, 1)

    def test_html_login_disguised_as_pdf_is_not_success(self):
        result = self.run_get(body=b'<html><form>Please sign in to continue</form></html>')
        self.assertEqual(result.status, 'restricted')
        self.assertIsNone(result.path)

    def test_non_pdf_body_is_not_complete_pdf(self):
        result = self.run_get(body=b'not a PDF document')
        self.assertEqual(result.status, 'unsupported')
        self.assertIsNone(result.path)

    def test_content_length_oversize_stops_before_read(self):
        response = FakeResponse(body=PDF, headers={'Content-Type': 'application/pdf', 'Content-Length': '1000'})
        with patch('linky.safe_http.SafeHTTPClient.open', return_value=response):
            result = acquire.acquire('https://example.com/a.pdf', self.root, limits=acquire.Limits(max_bytes=50))
        self.assertEqual(result.status, 'too_large')
        self.assertEqual(response.stream.tell(), 0)
        self.assertIsNone(result.path)

    def test_stream_limit_retains_only_bounded_partial_with_hash(self):
        result = self.run_get(limits=acquire.Limits(max_bytes=50))
        self.assertEqual(result.status, 'partial')
        self.assertTrue(result.partial)
        self.assertTrue(result.path.endswith('.partial'))
        self.assertEqual(result.size_bytes, 50)
        self.assertEqual((self.root / result.path).stat().st_size, 50)
        self.assertEqual(result.sha256, hashlib.sha256(PDF[:50]).hexdigest())

    def test_truncated_content_length_is_partial(self):
        result = self.run_get(headers={'Content-Type': 'application/pdf', 'Content-Length': str(len(PDF) + 10)})
        self.assertEqual(result.status, 'partial')

    def test_network_interruption_after_data_is_partial(self):
        response = FakeResponse(body=PDF, headers={'Content-Type': 'application/pdf'}, fail=True)
        with patch('linky.safe_http.SafeHTTPClient.open', return_value=response):
            result = acquire.acquire('https://example.com/a.pdf', self.root)
        self.assertEqual(result.status, 'partial')
        self.assertEqual(result.size_bytes, len(PDF))

    def test_unexpected_range_and_compressed_response_are_rejected(self):
        for response in [FakeResponse(status=206, body=PDF), FakeResponse(body=PDF, headers={'Content-Encoding':'gzip'})]:
            with patch('linky.safe_http.SafeHTTPClient.open', return_value=response):
                result = acquire.acquire('https://example.com/a.pdf', self.root)
            self.assertEqual(result.status, 'unsupported')

    def test_media_and_captions_need_explicit_intent(self):
        for url in ['https://example.com/a.mp4', 'https://example.com/a.vtt']:
            with patch('linky.safe_http.SafeHTTPClient.open') as request:
                result = acquire.acquire(url, self.root)
            self.assertEqual(result.status, 'needs_intent')
            request.assert_not_called()

    def test_explicit_direct_media_and_subtitles(self):
        cases = [('video', 'a.mp4', b'\x00\x00\x00\x18ftypmp42' + b'x'*20, 'video/mp4'),
                 ('subtitle','a.vtt', b'WEBVTT\n\n00:00.000 --> 00:01.000\nHello', 'text/vtt')]
        for kind, name, body, mime in cases:
            with self.subTest(kind=kind):
                result = self.run_get(url='https://example.com/'+name, body=body, headers={'Content-Type':mime}, allow_media=True)
                self.assertEqual(result.status, 'complete')

    def test_github_blob_normalizes_to_raw_without_gh(self):
        url = 'https://github.com/imarco/linky/blob/main/README.md'
        with patch('linky.safe_http.SafeHTTPClient.open', return_value=FakeResponse(body=b'# Readme', headers={'Content-Type':'text/plain'})) as request:
            result = acquire.acquire(url, self.root)
        self.assertEqual(result.status, 'complete')
        self.assertEqual(request.call_args.args[0], 'https://raw.githubusercontent.com/imarco/linky/main/README.md')
        self.assertEqual(result.source_url, url)

    def test_github_release_asset_is_opaque_never_unpacked(self):
        result = self.run_get(url='https://github.com/a/b/releases/download/v1/source.zip', body=b'PK\x03\x04not-unpacked', headers={'Content-Type':'application/octet-stream'})
        self.assertEqual(result.status, 'complete')
        self.assertEqual(result.kind, 'github_file')
        self.assertEqual(len(list(self.root.iterdir())), 2)

    def test_platform_pages_and_playlists_are_unsupported(self):
        for url in ['https://youtube.com/watch?v=a', 'https://example.com/a.m3u8', 'https://github.com/a/b/releases/tag/v1']:
            with patch('linky.safe_http.SafeHTTPClient.open') as request:
                result = acquire.acquire(url, self.root, allow_media=True)
            self.assertEqual(result.status, 'unsupported')
            request.assert_not_called()

    def test_article_images_are_opt_in_bounded_and_deduplicated(self):
        html = b'<html><img src="/a.png"><img src="/a.png"><img src="http://127.0.0.1/a.png"><img src="/b.png"></html>'
        calls = []
        def open_url(url):
            calls.append(url)
            return FakeResponse(body=html, headers={'Content-Type':'text/html'}) if url.endswith('/article') else FakeResponse(body=b'\x89PNG\r\n\x1a\n'+b'x'*20, headers={'Content-Type':'image/png'})
        with patch('linky.safe_http.SafeHTTPClient.open', side_effect=open_url):
            batch = acquire.acquire_batch(['https://example.com/article'], self.root, article_images=True, limits=acquire.Limits(max_files=3))
        self.assertEqual([r.status for r in batch.results], ['complete', 'complete', 'restricted'])
        self.assertEqual(len(calls), 2)
        self.assertEqual(batch.results[1].parent_url, 'https://example.com/article')
        self.assertTrue(batch.limited)

    def test_batch_budget_stops_further_downloads(self):
        with patch('linky.safe_http.SafeHTTPClient.open', return_value=FakeResponse(body=PDF, headers={'Content-Type':'application/pdf'})) as request:
            batch = acquire.acquire_batch(['https://example.com/a.pdf','https://example.com/b.pdf'], self.root, limits=acquire.Limits(max_total_bytes=len(PDF)))
        self.assertEqual(request.call_count, 1)
        self.assertTrue(batch.limited)

    def test_github_media_extension_still_requires_intent(self):
        with patch('linky.safe_http.SafeHTTPClient.open') as request:
            result = acquire.acquire('https://github.com/a/b/releases/download/v1/a.mp4', self.root)
        self.assertEqual(result.status, 'needs_intent')
        request.assert_not_called()

    def test_github_playlist_is_not_treated_as_opaque_download(self):
        with patch('linky.safe_http.SafeHTTPClient.open') as request:
            result = acquire.acquire('https://raw.githubusercontent.com/a/b/main/a.m3u8', self.root, allow_media=True)
        self.assertEqual(result.status, 'unsupported')
        request.assert_not_called()

    def test_invalid_media_body_is_not_success(self):
        result = self.run_get(url='https://example.com/a.mp4', body=b'not video', headers={'Content-Type':'video/mp4'}, allow_media=True)
        self.assertEqual(result.status, 'unsupported')

    def test_archive_read_rejects_replaced_symlink(self):
        archive = acquire.ArchiveDirectory(self.root)
        try:
            (self.root / 'victim').symlink_to('/etc/passwd')
            with self.assertRaises(OSError):
                archive.read('victim', 1024)
        finally:
            archive.close()

    def test_only_completed_results_can_enter_source_intake(self):
        complete = self.run_get()
        source = acquire.to_source_artifact(complete, self.root)
        self.assertEqual(source.original_uri, complete.source_url)
        self.assertEqual(source.metadata['sha256'], complete.sha256)
        self.assertEqual(source.artifact_path_or_text, str(self.root / complete.path))
        partial = self.run_get(limits=acquire.Limits(max_bytes=50))
        with self.assertRaises(ValueError):
            acquire.to_source_artifact(partial, self.root)

    def test_rejected_payloads_still_consume_batch_budget(self):
        def open_url(url):
            return FakeResponse(body=b'x'*100, headers={'Content-Type':'application/pdf'})
        with patch('linky.safe_http.SafeHTTPClient.open', side_effect=open_url) as request:
            batch = acquire.acquire_batch(['https://example.com/a.pdf', 'https://example.com/b.pdf'], self.root, limits=acquire.Limits(max_total_bytes=100))
        self.assertEqual(request.call_count, 1)
        self.assertTrue(batch.limited)
        self.assertEqual(batch.results[0].transferred_bytes, 100)

    def test_article_image_markup_cannot_request_arbitrary_release_file(self):
        html = b'<img src="https://github.com/a/b/releases/download/v1/run.exe">'
        def open_url(url):
            return FakeResponse(body=html, headers={'Content-Type':'text/html'}) if url.endswith('/article') else FakeResponse(body=b'MZ' + b'x'*30, headers={'Content-Type':'application/octet-stream'})
        with patch('linky.safe_http.SafeHTTPClient.open', side_effect=open_url):
            batch = acquire.acquire_batch(['https://example.com/article'], self.root, article_images=True)
        self.assertEqual(batch.results[1].status, 'unsupported')
        self.assertIsNone(batch.results[1].path)

    def test_chunked_content_length_conflict_is_rejected(self):
        result = self.run_get(headers={'Content-Type':'application/pdf', 'Transfer-Encoding':'chunked', 'Content-Length':'10'}, limits=acquire.Limits(max_bytes=10))
        self.assertEqual(result.status, 'unsupported')
        self.assertIsNone(result.path)

    def test_image_expectation_always_checks_image_signature(self):
        result = self.run_get(headers={'Content-Type':'image/png'}, expected_kind='image')
        self.assertEqual(result.status, 'unsupported')
        self.assertIsNone(result.path)

    def test_playlist_mime_cannot_hide_in_opaque_github_resource(self):
        for mime in ['application/vnd.apple.mpegurl', 'application/x-mpegurl', 'audio/mpegurl', 'application/dash+xml']:
            with self.subTest(mime=mime):
                result = self.run_get(url='https://github.com/a/b/releases/download/v1/file', body=b'#EXTM3U', headers={'Content-Type':mime}, allow_media=True)
                self.assertEqual(result.status, 'unsupported')

    def test_output_directory_rejects_shared_write_permissions(self):
        self.root.chmod(0o777)
        try:
            with self.assertRaises(ValueError):
                acquire.acquire('https://example.com/a.pdf', self.root)
        finally:
            self.root.chmod(0o700)

    def test_redirected_media_requires_intent_even_when_mime_is_opaque(self):
        response = FakeResponse(body=b'video', headers={'Content-Type':'application/octet-stream'})
        response.url = 'https://example.com/a.mp4'
        with patch('linky.safe_http.SafeHTTPClient.open', return_value=response):
            result = acquire.acquire('https://github.com/a/b/releases/download/v1/file', self.root)
        self.assertEqual(result.status, 'needs_intent')
        self.assertEqual(response.stream.tell(), 0)

    def test_github_html_file_can_be_archived_and_discover_images(self):
        html = b'<html><img src="./image.png"></html>'
        def open_url(url):
            response = FakeResponse(body=html if url.endswith('.html') else b'\x89PNG\r\n\x1a\n'+b'x'*20, headers={'Content-Type':'text/plain' if url.endswith('.html') else 'image/png'})
            response.url = url
            return response
        with patch('linky.safe_http.SafeHTTPClient.open', side_effect=open_url):
            batch = acquire.acquire_batch(['https://raw.githubusercontent.com/a/b/main/article.html'], self.root, article_images=True)
        self.assertEqual([r.status for r in batch.results], ['complete', 'complete'])
        self.assertEqual(batch.results[1].kind, 'image')

    def test_cli_requires_url_and_exposes_bounds(self):
        proc = subprocess.run([sys.executable, str(ROOT/'bin/linky-get'), '--help'], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn('--allow-media', proc.stdout)
        self.assertIn('--article-images', proc.stdout)

if __name__ == '__main__':
    unittest.main()
