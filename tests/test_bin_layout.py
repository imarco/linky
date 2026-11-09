"""Operation entrypoints must keep initialization and legacy callers working."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINTS = ("bin/init-config.sh", "scripts/init-config.sh")


class ConfigEntrypointTests(unittest.TestCase):
    def run_init(self, entrypoint: str, home: Path) -> None:
        script = ROOT / entrypoint
        self.assertTrue(script.is_file(), f"Missing entrypoint: {entrypoint}")
        proc = subprocess.run(
            [str(script)],
            cwd=home,
            env={**os.environ, "HOME": str(home)},
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_entrypoints_initialize_config_from_another_directory(self):
        for entrypoint in ENTRYPOINTS:
            with self.subTest(entrypoint=entrypoint), tempfile.TemporaryDirectory() as tmp:
                home = Path(tmp)
                self.run_init(entrypoint, home)
                config = home / ".config" / "linky"
                self.assertIn('default_output = "markdown"', (config / "config.toml").read_text())
                for name in ("fetch-strategy.toml", "user-profile.toml"):
                    source = "user-profile-template.toml" if name == "user-profile.toml" else name
                    self.assertEqual((config / name).read_bytes(), (ROOT / "references" / source).read_bytes())
                self.assertTrue((config / "personas" / "default.md").is_file())
                self.assertTrue((config / "memory.md").is_file())

    def test_entrypoints_preserve_custom_config_on_repeat(self):
        for entrypoint in ENTRYPOINTS:
            with self.subTest(entrypoint=entrypoint), tempfile.TemporaryDirectory() as tmp:
                home = Path(tmp)
                self.run_init(entrypoint, home)
                config = home / ".config" / "linky"
                files = ("config.toml", "fetch-strategy.toml", "user-profile.toml", "memory.md")
                for name in files:
                    (config / name).write_text(f"custom {name}\n")
                self.run_init(entrypoint, home)
                for name in files:
                    self.assertEqual((config / name).read_text(), f"custom {name}\n")


if __name__ == "__main__":
    unittest.main()
