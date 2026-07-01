import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from linky.providers.platforms import (
    clean_xhs_note,
    feed_to_markdown,
    github_repo_to_markdown,
    v2ex_topic_to_markdown,
    youtube_info_to_markdown,
)


class PlatformProviderParserTests(unittest.TestCase):
    def test_youtube_info_to_markdown_keeps_transcript_and_metadata(self):
        markdown, metadata = youtube_info_to_markdown(
            {
                "title": "Demo Video",
                "channel": "Example Channel",
                "duration": 120,
                "upload_date": "20260626",
                "webpage_url": "https://www.youtube.com/watch?v=abc",
                "subtitles_text": "Hello from captions. " * 20,
            }
        )

        self.assertIn("# Demo Video", markdown)
        self.assertIn("Hello from captions.", markdown)
        self.assertEqual(metadata["channel"], "Example Channel")
        self.assertEqual(metadata["duration"], 120)

    def test_github_repo_to_markdown_keeps_repo_fields(self):
        markdown, metadata = github_repo_to_markdown(
            {
                "nameWithOwner": "imarco/linky",
                "description": "Link research tool",
                "url": "https://github.com/imarco/linky",
                "stargazerCount": 42,
                "primaryLanguage": {"name": "Python"},
            }
        )

        self.assertIn("# imarco/linky", markdown)
        self.assertIn("Link research tool", markdown)
        self.assertEqual(metadata["stars"], 42)

    def test_feed_to_markdown_keeps_entries(self):
        markdown, metadata = feed_to_markdown(
            {
                "feed": {"title": "Example Feed", "link": "https://example.com/feed"},
                "entries": [
                    {
                        "title": "Entry One",
                        "link": "https://example.com/one",
                        "summary": "Useful feed entry summary. " * 8,
                    }
                ],
            }
        )

        self.assertIn("# Example Feed", markdown)
        self.assertIn("Entry One", markdown)
        self.assertEqual(metadata["entry_count"], 1)

    def test_v2ex_topic_to_markdown_keeps_replies(self):
        markdown, metadata = v2ex_topic_to_markdown(
            {
                "id": 123,
                "title": "Python discussion",
                "content": "Topic body with enough useful details. " * 8,
                "url": "https://www.v2ex.com/t/123",
                "member": {"username": "alice"},
                "node": {"name": "python", "title": "Python"},
                "replies": [
                    {"author": "bob", "content": "Reply text with useful details. " * 4, "created": 1},
                ],
            }
        )

        self.assertIn("# Python discussion", markdown)
        self.assertIn("Reply text", markdown)
        self.assertEqual(metadata["node_name"], "python")

    def test_clean_xhs_note_strips_redundant_fields(self):
        cleaned = clean_xhs_note(
            {
                "note_card": {
                    "note_id": "n1",
                    "title": "Title",
                    "desc": "Body",
                    "user": {"nickname": "Alice", "user_id": "u1", "avatar": "drop"},
                    "interact_info": {"liked_count": 5, "ignored": 1},
                    "image_list": [{"url": "https://img"}],
                    "tag_list": [{"name": "tag"}],
                },
                "massive": {"ignored": True},
            }
        )

        self.assertEqual(cleaned["note_id"], "n1")
        self.assertEqual(cleaned["user"]["nickname"], "Alice")
        self.assertNotIn("massive", cleaned)


if __name__ == "__main__":
    unittest.main()
