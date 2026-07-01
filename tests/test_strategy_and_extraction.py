import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from linky.extract import extract_url
from linky.extract import _tweet_json_to_markdown, _vxtwitter_provider
from linky.strategy import load_strategy, provider_config, resolve_provider_chain, trace_enabled


class StrategyAndExtractionTests(unittest.TestCase):
    def setUp(self):
        self.strategy = load_strategy(ROOT / "references" / "fetch-strategy.toml")

    def test_loads_fallback_chain_from_toml(self):
        chain = resolve_provider_chain("https://example.com/post", self.strategy)

        self.assertEqual(chain[:3], ["jina", "trafilatura", "scrapling"])
        self.assertTrue(trace_enabled(self.strategy))

    def test_domain_route_override_skips_layers(self):
        chain = resolve_provider_chain("https://mp.weixin.qq.com/s/example", self.strategy)

        self.assertEqual(chain[0], "scrapling")
        self.assertNotIn("jina", chain)

    def test_x_domain_route_prefers_vxtwitter_provider(self):
        chain = resolve_provider_chain("https://x.com/example/status/1234567890", self.strategy)

        self.assertEqual(chain[0], "vxtwitter")
        self.assertNotIn("jina", chain)

    def test_provider_config_reads_dedicated_platform_provider(self):
        provider = provider_config(self.strategy, "youtube_ytdlp")

        self.assertEqual(provider["method"], "command-json")
        self.assertIn("yt-dlp", provider["requires"])
        self.assertEqual(provider["role"], "transcript")

    def test_youtube_domain_route_prefers_ytdlp_provider(self):
        chain = resolve_provider_chain("https://www.youtube.com/watch?v=dQw4w9WgXcQ", self.strategy)

        self.assertEqual(chain[0], "youtube_ytdlp")
        self.assertNotIn("jina", chain[:1])

    def test_bilibili_route_never_uses_ytdlp(self):
        chain = resolve_provider_chain("https://www.bilibili.com/video/BV123", self.strategy)

        self.assertEqual(chain[0], "bilibili_cli")
        self.assertNotIn("youtube_ytdlp", chain)

    def test_vxtwitter_json_formats_tweet_markdown(self):
        markdown, metadata = _tweet_json_to_markdown(
            {
                "text": "A useful public tweet about Linky extraction.",
                "user_name": "Example User",
                "user_screen_name": "example",
                "likes": 42,
                "retweets": 7,
                "replies": 3,
                "date": "Sat May 30 13:15:16 +0000 2026",
                "mediaURLs": ["https://cdn.example/image.jpg"],
                "tweetURL": "https://x.com/example/status/1234567890",
            }
        )

        self.assertIn("# Example User (@example)", markdown)
        self.assertIn("A useful public tweet about Linky extraction.", markdown)
        self.assertIn("![media 1](https://cdn.example/image.jpg)", markdown)
        self.assertEqual(metadata["tweet_url"], "https://x.com/example/status/1234567890")
        self.assertEqual(metadata["media_count"], 1)

    def test_vxtwitter_json_prefers_article_blocks(self):
        markdown, metadata = _tweet_json_to_markdown(
            {
                "tweet": {
                    "text": "https://t.co/article",
                    "author": {"name": "Poteto", "screen_name": "poteto"},
                    "article": {
                        "title": "How I use Cursor",
                        "content": {
                            "blocks": [
                                {"type": "header-two", "text": "Workflow"},
                                {"type": "paragraph", "text": "I keep planning and execution separate."},
                                {"type": "unordered-list-item", "text": "Use real payload block types"},
                                {"type": "list", "items": ["Capture source", "Write notes"]},
                            ]
                        },
                    },
                    "tweetURL": "https://x.com/poteto/status/1234567890",
                }
            }
        )

        self.assertIn("# How I use Cursor", markdown)
        self.assertIn("Author: Poteto (@poteto)", markdown)
        self.assertIn("## Workflow", markdown)
        self.assertIn("I keep planning and execution separate.", markdown)
        self.assertIn("- Use real payload block types", markdown)
        self.assertIn("- Capture source", markdown)
        self.assertEqual(metadata["content_type"], "article")

    def test_vxtwitter_provider_builds_api_url_and_reads_json(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b'{"text":"Fetched tweet body with enough useful content for extraction.","tweetURL":"https://x.com/example/status/1234567890"}'

        with patch("linky.extract.urllib.request.urlopen", return_value=FakeResponse()) as urlopen:
            result = _vxtwitter_provider(
                "https://x.com/example/status/1234567890",
                {"api_pattern": "https://api.vxtwitter.com/{screen_name}/status/{tweet_id}"},
                {"global": {"timeout_seconds": 5}},
            )

        self.assertIn("Fetched tweet body", result["markdown"])
        self.assertEqual(result["metadata"]["tweet_id"], "1234567890")
        self.assertEqual(result["metadata"]["screen_name"], "example")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.vxtwitter.com/example/status/1234567890")

    def test_quality_driven_fallback_records_trace(self):
        def bad_provider(url, provider, strategy):
            return {"markdown": "login", "metadata": {"name": "bad"}}

        def good_provider(url, provider, strategy):
            return {
                "markdown": "# Good Article\n\n"
                "This useful article has enough text and source metadata.\n\n"
                "It contains several paragraphs for scoring.\n\n"
                "Published by Example with a [source](https://example.com).",
                "metadata": {"name": "good"},
            }

        strategy = {
            "global": {"quality_threshold": 0.55},
            "fallback_chain": [{"id": "bad"}, {"id": "good"}],
            "quality": {"min_score": 0.55},
        }

        result = extract_url(
            "https://example.com",
            strategy=strategy,
            providers={"bad": bad_provider, "good": good_provider},
        )

        self.assertEqual(result.status, "success")
        self.assertEqual(result.provider, "good")
        self.assertEqual(result.trace.attempts[0].fallback_reason, "low_quality")
        self.assertEqual(result.trace.final_provider, "good")

    def test_legacy_scrapling_cli_help_is_compatible(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "scrapling_fetch.py"), "--help"],
            check=False,
            text=True,
            capture_output=True,
        )

        self.assertEqual(proc.returncode, 0)
        self.assertIn("scrapling_fetch.py", proc.stdout)

    def test_legacy_scrapling_function_is_import_compatible(self):
        import scripts.scrapling_fetch as scrapling_fetch

        self.assertTrue(callable(scrapling_fetch.fetch_and_extract))

    def test_browser_command_provider_executes_configured_command(self):
        strategy = {
            "global": {"quality_threshold": 0.55, "timeout_seconds": 5, "max_chars": 30000},
            "fallback_chain": [
                {
                    "id": "browser",
                    "command": (
                        "python3 -c \"print('# Browser Page\\n\\n"
                        "This browser fallback page has source metadata.\\n\\n"
                        "It includes enough paragraphs for quality scoring.\\n\\n"
                        "Published by Linky with a [source](https://example.com).')\""
                    ),
                }
            ],
            "quality": {"min_score": 0.55},
        }

        result = extract_url("https://example.com/browser-only", strategy=strategy)

        self.assertEqual(result.status, "success")
        self.assertEqual(result.provider, "browser")
        self.assertEqual(result.trace.final_provider, "browser")

    def test_platform_provider_can_be_registered_by_id(self):
        def youtube_provider(url, provider, strategy):
            return {
                "markdown": "# Video\n\n"
                "Author: Example.\n\n"
                "Transcript with enough source metadata. " * 12
                + "\n\n[source](https://youtu.be/x)",
                "metadata": {"provider": "youtube_ytdlp"},
            }

        strategy = {
            "global": {"quality_threshold": 0.55},
            "quality": {"min_score": 0.55},
            "providers": {"youtube_ytdlp": {"id": "youtube_ytdlp"}},
            "domain_routes": [{"pattern": "youtube.com", "go_to": "youtube_ytdlp", "skip_layers": ["jina"]}],
            "fallback_chain": [{"id": "jina"}],
        }

        result = extract_url(
            "https://www.youtube.com/watch?v=x",
            strategy=strategy,
            providers={"youtube_ytdlp": youtube_provider},
        )

        self.assertEqual(result.status, "success")
        self.assertEqual(result.provider, "youtube_ytdlp")

    def test_youtube_provider_runs_ytdlp_and_normalizes_output(self):
        proc = subprocess.CompletedProcess(
            ["yt-dlp"],
            0,
            stdout=(
                '{"title":"Demo Video","channel":"Example Channel","duration":120,'
                '"upload_date":"20260626","webpage_url":"https://www.youtube.com/watch?v=x",'
                '"subtitles_text":"Transcript body with useful details. Transcript body with useful details. '
                'Transcript body with useful details. Transcript body with useful details. '
                'Transcript body with useful details. Transcript body with useful details."}'
            ),
            stderr="",
        )

        with patch("linky.extract.subprocess.run", return_value=proc):
            result = extract_url("https://www.youtube.com/watch?v=x", strategy=self.strategy)

        self.assertEqual(result.status, "success")
        self.assertEqual(result.provider, "youtube_ytdlp")
        self.assertIn("Transcript body", result.markdown)
        self.assertEqual(result.trace.final_provider, "youtube_ytdlp")

    def test_github_provider_runs_gh_and_normalizes_repo_output(self):
        proc = subprocess.CompletedProcess(
            ["gh"],
            0,
            stdout=(
                '{"nameWithOwner":"imarco/linky","description":"Link research tool with enough useful details. '
                'It explains source intake, extraction, traces, reports, and durable notes.",'
                '"url":"https://github.com/imarco/linky","stargazerCount":42,'
                '"primaryLanguage":{"name":"Python"}}'
            ),
            stderr="",
        )

        with patch("linky.extract.subprocess.run", return_value=proc):
            result = extract_url("https://github.com/imarco/linky", strategy=self.strategy)

        self.assertEqual(result.status, "success")
        self.assertEqual(result.provider, "github_gh")
        self.assertIn("# imarco/linky", result.markdown)

    def test_rss_provider_uses_feedparser_when_available(self):
        class FakeFeedparser:
            @staticmethod
            def parse(url):
                return {
                    "feed": {"title": "Example Feed", "link": url},
                    "entries": [
                        {
                            "title": "Entry One",
                            "link": "https://example.com/one",
                            "summary": "Useful feed entry summary with enough context. " * 8,
                        }
                    ],
                }

        strategy = {
            "global": {"quality_threshold": 0.55},
            "quality": {"min_score": 0.55},
            "providers": {"rss_feedparser": {"id": "rss_feedparser"}},
            "domain_routes": [{"pattern": "example.com", "go_to": "rss_feedparser", "skip_layers": ["jina"]}],
            "fallback_chain": [{"id": "jina"}],
        }

        with patch.dict(sys.modules, {"feedparser": FakeFeedparser}):
            result = extract_url("https://example.com/feed.xml", strategy=strategy)

        self.assertEqual(result.status, "success")
        self.assertEqual(result.provider, "rss_feedparser")
        self.assertIn("Entry One", result.markdown)

    def test_v2ex_provider_fetches_topic_and_replies(self):
        class FakeResponse:
            def __init__(self, body):
                self.body = body

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return self.body.encode("utf-8")

        def fake_urlopen(request, timeout=0):
            if "topics/show" in request.full_url:
                return FakeResponse(
                    '[{"id":123,"title":"Python discussion","content":"Topic body with enough useful details. '
                    'Topic body with enough useful details. Topic body with enough useful details.",'
                    '"url":"https://www.v2ex.com/t/123","member":{"username":"alice"},'
                    '"node":{"name":"python","title":"Python"}}]'
                )
            return FakeResponse(
                '[{"author":"bob","content":"Reply text with useful details. Reply text with useful details."}]'
            )

        with patch("linky.extract.urllib.request.urlopen", side_effect=fake_urlopen):
            result = extract_url("https://www.v2ex.com/t/123", strategy=self.strategy)

        self.assertEqual(result.status, "success")
        self.assertEqual(result.provider, "v2ex_api")
        self.assertIn("Reply text", result.markdown)


if __name__ == "__main__":
    unittest.main()
