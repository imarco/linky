import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from linky.doctor import doctor_report
from linky.intake import SourceKind, detect_source_kind, intake_source, intake_sources


class SourceIntakeTests(unittest.TestCase):
    def test_detect_source_kind(self):
        self.assertEqual(detect_source_kind("https://example.com/a"), SourceKind.URL)
        self.assertEqual(detect_source_kind("notes.md"), SourceKind.MARKDOWN)
        self.assertEqual(detect_source_kind("notes.txt"), SourceKind.TEXT)
        self.assertEqual(detect_source_kind("paper.pdf"), SourceKind.PDF)
        self.assertEqual(detect_source_kind("deck.pptx"), SourceKind.OFFICE)
        self.assertEqual(detect_source_kind("archive.zip"), SourceKind.UNSUPPORTED)

    def test_url_pass_through(self):
        artifact = intake_source("https://example.com/article")

        self.assertEqual(artifact.kind, SourceKind.URL)
        self.assertEqual(artifact.status, "success")
        self.assertEqual(artifact.artifact_path_or_text, "https://example.com/article")
        self.assertEqual(artifact.metadata["extraction_pipeline"], "existing_url_pipeline")
        self.assertEqual(artifact.trace.final_status, "success")
        self.assertIn("trace", artifact.to_dict())

    def test_markdown_and_text_files_become_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            md = root / "note.md"
            txt = root / "note.txt"
            md.write_text("# Title\n\nMarkdown body", encoding="utf-8")
            txt.write_text("Plain text body", encoding="utf-8")

            md_artifact = intake_source(str(md))
            txt_artifact = intake_source(str(txt))

        self.assertEqual(md_artifact.status, "success")
        self.assertEqual(md_artifact.kind, SourceKind.MARKDOWN)
        self.assertIn("Markdown body", md_artifact.artifact_path_or_text)
        self.assertEqual(txt_artifact.status, "success")
        self.assertEqual(txt_artifact.kind, SourceKind.TEXT)
        self.assertIn("Plain text body", txt_artifact.artifact_path_or_text)

    def test_missing_path_fails_without_throwing(self):
        artifact = intake_source("/tmp/does-not-exist-linky-source.md")

        self.assertEqual(artifact.status, "failed")
        self.assertTrue(artifact.errors)
        self.assertEqual(artifact.trace.final_status, "failed")

    def test_unsupported_extension_returns_unsupported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "archive.zip"
            path.write_text("zip-ish", encoding="utf-8")
            artifact = intake_source(str(path))

        self.assertEqual(artifact.status, "unsupported")
        self.assertEqual(artifact.kind, SourceKind.UNSUPPORTED)
        self.assertTrue(artifact.errors)

    def test_missing_markitdown_is_structured_dependency_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "paper.pdf"
            path.write_bytes(b"%PDF test")
            artifact = intake_source(str(path), dependency_checker=lambda name: False)

        self.assertEqual(artifact.kind, SourceKind.PDF)
        self.assertEqual(artifact.status, "missing_dependency")
        self.assertIn("markitdown", artifact.errors[0])
        self.assertEqual(artifact.trace.final_status, "missing_dependency")

    def test_convertible_file_uses_injected_converter(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "paper.pdf"
            path.write_bytes(b"%PDF test")
            artifact = intake_source(str(path), converter=lambda file_path: "# Converted\n\nBody")

        self.assertEqual(artifact.status, "success")
        self.assertEqual(artifact.artifact_path_or_text, "# Converted\n\nBody")
        self.assertEqual(artifact.metadata["converter"], "markitdown")

    def test_batch_intake_keeps_recoverable_failures_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            md = root / "note.md"
            pdf = root / "paper.pdf"
            md.write_text("# Title", encoding="utf-8")
            pdf.write_bytes(b"%PDF test")

            artifacts = intake_sources([str(md), str(pdf)], dependency_checker=lambda name: False)

        self.assertEqual([artifact.status for artifact in artifacts], ["success", "missing_dependency"])


class DoctorTests(unittest.TestCase):
    def test_doctor_reports_ready_missing_and_disabled(self):
        strategy = {
            "fallback_chain": [
                {"id": "jina"},
                {"id": "trafilatura", "requires": ["trafilatura"]},
                {"id": "browser", "requires": ["playwright-cli"]},
                {"id": "disabled-provider", "enabled": False, "requires": ["missing_mod"]},
            ]
        }

        report = doctor_report(
            strategy=strategy,
            module_checker=lambda name: name in {"markitdown"},
            command_checker=lambda name: False,
        )

        providers = {item["id"]: item for item in report["providers"]}
        self.assertEqual(providers["jina"]["status"], "ready")
        self.assertEqual(providers["trafilatura"]["status"], "missing")
        self.assertEqual(providers["browser"]["status"], "missing")
        self.assertEqual(providers["disabled-provider"]["status"], "disabled")
        self.assertEqual(report["modules"]["markitdown"], "ready")
        self.assertEqual(report["commands"]["playwright-cli"], "missing")
        self.assertEqual(report["status"], "missing")

    def test_doctor_reads_repository_strategy(self):
        report = doctor_report(
            ROOT / "references" / "fetch-strategy.toml",
            module_checker=lambda name: True,
            command_checker=lambda name: True,
        )

        provider_ids = [item["id"] for item in report["providers"]]
        self.assertIn("jina", provider_ids)
        self.assertIn("scrapling", provider_ids)
        self.assertEqual(report["status"], "ready")

    def test_doctor_cli_help_is_compatible(self):
        proc = subprocess.run(
            [str(ROOT / "bin" / "linky-doctor"), "--help"],
            check=False,
            text=True,
            capture_output=True,
        )

        self.assertEqual(proc.returncode, 0)
        self.assertIn("linky-doctor", proc.stdout)


if __name__ == "__main__":
    unittest.main()
