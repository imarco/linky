import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from linky.doctor import doctor_report
from linky.extract import _github_gh_provider, _rss_feedparser_provider, _youtube_ytdlp_provider, extract_url
from linky.strategy import load_strategy, resolve_provider_chain


class ProviderRegressionTests(unittest.TestCase):
    def test_youtube_reads_selected_json3_captions(self):
        info = {
            "title": "Demo", "webpage_url": "https://www.youtube.com/watch?v=demo",
            "requested_subtitles": {"en": {"ext": "json3", "url": "https://www.youtube.com/api/timedtext?v=demo"}},
        }
        captions = {"events": [{"segs": [{"utf8": "Hello "}, {"utf8": "world."}]}, {"segs": [{"utf8": "Second sentence."}]}]}
        with patch("linky.extract._run_json_command", return_value=info) as command, patch("linky.extract._fetch_json", return_value=captions) as fetch:
            result = _youtube_ytdlp_provider(info["webpage_url"], {"sub_lang": "en"}, {"global": {"timeout_seconds": 7}})

        self.assertIn("Hello world.", result["markdown"])
        self.assertIn("Second sentence.", result["markdown"])
        self.assertEqual(result["metadata"]["subtitle_language"], "en")
        args, timeout = command.call_args.args
        self.assertIn("--simulate", args)
        self.assertIn("--no-playlist", args)
        self.assertIn("--write-subs", args)
        self.assertIn("--write-auto-subs", args)
        self.assertIn("json3", args)
        self.assertIn("--js-runtimes", args)
        self.assertEqual(timeout, 7)
        fetch.assert_called_once_with(info["requested_subtitles"]["en"]["url"], 7)

    def test_youtube_without_captions_does_not_claim_transcript(self):
        for subtitles in (None, {}, {"en": {"ext": "vtt", "url": "https://example.com/captions"}}):
            with self.subTest(subtitles=subtitles), patch("linky.extract._run_json_command", return_value={"title": "A long title " * 60, "requested_subtitles": subtitles}):
                with self.assertRaisesRegex(RuntimeError, "caption"):
                    _youtube_ytdlp_provider("https://youtu.be/demo", {}, {})

    def test_youtube_empty_caption_payload_is_rejected(self):
        info = {"requested_subtitles": {"en": {"ext": "json3", "url": "https://www.youtube.com/api/timedtext"}}}
        for payload in ({"events": []}, {"events": [{"segs": [{"utf8": "\n"}]}]}, {"error": "not captions"}):
            with self.subTest(payload=payload), patch("linky.extract._run_json_command", return_value=info), patch("linky.extract._fetch_json", return_value=payload):
                with self.assertRaisesRegex(RuntimeError, "caption"):
                    _youtube_ytdlp_provider("https://youtu.be/demo", {}, {})

    def test_github_unsupported_paths_do_not_return_repo_summary(self):
        for url in ("https://github.com/a/b/blob/main/file.py", "https://github.com/a/b/tree/main", "https://github.com/a/b/releases/tag/v1", "https://github.com/a/b/issues", "https://github.com/a/b/pull/not-a-number", "https://example.com/a/b"):
            with self.subTest(url=url), patch("linky.extract._run_json_command") as command:
                with self.assertRaises(RuntimeError):
                    _github_gh_provider(url, {}, {})
                command.assert_not_called()

    def test_github_unsupported_path_falls_back_with_trace(self):
        strategy = {"domain_routes": [{"pattern": "github.com", "go_to": "github_gh"}], "fallback_chain": [{"id": "fallback"}]}
        body = "# Requested file\n\nSource: actual file body. " + "Useful explanation. " * 40
        with patch("linky.extract._run_json_command") as command:
            result = extract_url("https://github.com/a/b/blob/main/README.md", strategy=strategy, providers={"fallback": lambda *_: body})
        self.assertEqual(result.provider, "fallback")
        self.assertEqual(result.trace.attempts[0].status, "failed")
        command.assert_not_called()

    def test_rss_fetch_has_configured_timeout_and_parses_bytes(self):
        raw = b'<rss version="2.0"><channel><title>Feed</title></channel></rss>'
        parse = MagicMock(return_value={"version": "rss20", "feed": {"title": "Feed"}, "entries": []})
        response = MagicMock()
        response.__enter__.return_value.read.return_value = raw
        with patch.dict(sys.modules, {"feedparser": SimpleNamespace(parse=parse)}), patch("linky.extract.urllib.request.urlopen", return_value=response) as urlopen:
            result = _rss_feedparser_provider("https://example.com/feed.xml", {}, {"global": {"timeout_seconds": 7}})
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 7)
        self.assertEqual(parse.call_args.args[0], raw)
        self.assertIn("Feed", result["markdown"])

    def test_rss_html_response_is_rejected(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b"<html>not a feed</html>"
        with patch.dict(sys.modules, {"feedparser": SimpleNamespace(parse=lambda *_, **kwargs: {"version": "", "feed": {}, "entries": []})}), patch("linky.extract.urllib.request.urlopen", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "feed"):
                _rss_feedparser_provider("https://example.com/feed", {}, {})

    @unittest.skipUnless(importlib.util.find_spec("feedparser"), "optional feedparser is not installed")
    def test_rss_relative_links_keep_the_response_base_url(self):
        response = MagicMock()
        response.__enter__.return_value.geturl.return_value = "https://example.com/news/feed.xml"
        response.__enter__.return_value.read.return_value = (
            b'<feed xmlns="http://www.w3.org/2005/Atom"><title>News</title>'
            b'<entry><title>Story</title><link href="story"/>'
            b'<summary>Article summary</summary></entry></feed>'
        )
        with patch("linky.extract.urllib.request.urlopen", return_value=response):
            result = _rss_feedparser_provider("https://example.com/feed", {}, {})
        self.assertIn("https://example.com/news/story", result["markdown"])

    def test_feed_urls_use_feedparser_without_overriding_explicit_routes(self):
        strategy = load_strategy(ROOT / "references/fetch-strategy.toml")
        for path in ("/feed", "/feed/", "/feed.xml", "/index.rss", "/atom.xml?format=atom"):
            with self.subTest(path=path):
                self.assertEqual(resolve_provider_chain("https://example.com" + path, strategy)[0], "rss_feedparser")
        self.assertEqual(resolve_provider_chain("https://example.com/post", strategy)[0], "jina")
        self.assertEqual(resolve_provider_chain("https://github.com/a/b/blob/main/feed.xml", strategy)[0], "github_gh")

    def test_disabled_provider_is_not_executed(self):
        strategy = {"fallback_chain": [{"id": "disabled", "enabled": False}, {"id": "fallback"}], "domain_routes": [{"pattern": "example.com", "go_to": "disabled"}]}
        disabled = MagicMock(side_effect=AssertionError("disabled provider executed"))
        result = extract_url("https://example.com/post", strategy=strategy, providers={"disabled": disabled, "fallback": lambda *_: "# Actual content\n\n" + "Source details. " * 60})
        disabled.assert_not_called()
        self.assertEqual(result.provider, "fallback")

    def test_max_chars_applies_to_native_provider_results(self):
        body = "# Heading\n\nSource: body\n\n" + "Content paragraph. " * 60
        result = extract_url("https://example.com/post", strategy={"global": {"max_chars": 200}, "fallback_chain": [{"id": "fake"}]}, providers={"fake": lambda *_: {"markdown": body}})
        self.assertEqual(result.markdown, body[:200])
        self.assertEqual(result.trace.attempts[0].content_length, 200)

    def test_installed_cli_does_not_make_unimplemented_provider_ready(self):
        report = doctor_report(strategy={"providers": {"opencli_xhs": {"requires": ["opencli"]}}}, module_checker=lambda _: True, command_checker=lambda _: True)
        self.assertEqual(report["providers"][0]["status"], "unimplemented")
        self.assertNotEqual(report["status"], "ready")


if __name__ == "__main__":
    unittest.main()
