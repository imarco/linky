import contextlib
import io
import runpy
import subprocess
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


class InstallScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.install = runpy.run_path(str(ROOT / "bin" / "install"), run_name="linky_install_test")
        cls.globals = cls.install["main"].__globals__

    def run_main(self, argv, *, commands, modules, available_commands=None, available_modules=None, run=None):
        available_commands = available_commands if isinstance(available_commands, set) else set(available_commands or ())
        available_modules = available_modules if isinstance(available_modules, set) else set(available_modules or ())

        def which(name):
            return f"/fake/bin/{name}" if name in available_commands else None

        def module_available(name):
            return name in available_modules

        output = io.StringIO()
        run_mock = mock.Mock(side_effect=run) if run is not None else mock.Mock()
        with (
            mock.patch.dict(self.globals, {"COMMANDS": commands, "MODULES": modules}, clear=False),
            mock.patch.dict(self.globals, {"_module_available": module_available}, clear=False),
            mock.patch.object(self.globals["shutil"], "which", side_effect=which),
            mock.patch.object(self.globals["subprocess"], "run", run_mock),
            contextlib.redirect_stdout(output),
        ):
            status = self.install["main"](argv)
        return status, output.getvalue(), run_mock

    def test_check_reports_missing_dependencies_without_running_subprocess(self):
        commands = {
            "yt-dlp": {
                "auto": ["pipx", "install", "yt-dlp"],
                "manual": "pipx install yt-dlp",
            }
        }
        modules = {
            "feedparser": {
                "auto": [self.globals["sys"].executable, "-m", "pip", "install", "feedparser"],
                "manual": "Install feedparser into Linky's Python environment.",
            }
        }

        status, output, run_mock = self.run_main(
            ["--check"],
            commands=commands,
            modules=modules,
        )

        self.assertEqual(status, 1)
        self.assertIn("missing command: yt-dlp", output)
        self.assertIn("missing module: feedparser", output)
        run_mock.assert_not_called()

    def test_check_and_install_are_mutually_exclusive(self):
        with self.assertRaises(SystemExit) as raised:
            self.install["main"](["--check", "--install"])

        self.assertEqual(raised.exception.code, 2)

    def test_install_returns_nonzero_and_prints_manual_action_after_command_failure(self):
        commands = {
            "yt-dlp": {
                "auto": ["pipx", "install", "yt-dlp"],
                "manual": "pipx install yt-dlp",
            }
        }
        modules = {}

        def failed_install(command, check=False):
            return subprocess.CompletedProcess(command, 7)

        status, output, run_mock = self.run_main(
            ["--install"],
            commands=commands,
            modules=modules,
            available_commands={"pipx"},
            run=failed_install,
        )

        self.assertEqual(status, 1)
        run_mock.assert_called_once_with(["pipx", "install", "yt-dlp"], check=False)
        self.assertIn("install failed for yt-dlp", output)
        self.assertIn("pipx install yt-dlp", output)
        self.assertIn("still missing command: yt-dlp", output)

    def test_install_does_not_report_success_when_command_install_is_a_false_success(self):
        commands = {
            "opencli": {
                "auto": ["npm", "install", "-g", "@jackwener/opencli"],
                "manual": "npm install -g @jackwener/opencli",
            }
        }
        modules = {}

        def false_success(command, check=False):
            return subprocess.CompletedProcess(command, 0)

        status, output, run_mock = self.run_main(
            ["--install"],
            commands=commands,
            modules=modules,
            available_commands={"npm"},
            run=false_success,
        )

        self.assertEqual(status, 1)
        run_mock.assert_called_once_with(
            ["npm", "install", "-g", "@jackwener/opencli"],
            check=False,
        )
        self.assertIn("still missing command: opencli", output)

    def test_install_handles_missing_executable_without_traceback(self):
        commands = {
            "yt-dlp": {
                "auto": ["pipx", "install", "yt-dlp"],
                "manual": "pipx install yt-dlp",
            }
        }
        modules = {}

        def missing_executable(command, check=False):
            raise FileNotFoundError(2, "No such file or directory", command[0])

        status, output, run_mock = self.run_main(
            ["--install"],
            commands=commands,
            modules=modules,
            available_commands={"pipx"},
            run=missing_executable,
        )

        self.assertEqual(status, 1)
        run_mock.assert_called_once_with(["pipx", "install", "yt-dlp"], check=False)
        self.assertIn("install failed for yt-dlp", output)
        self.assertIn("manual install required for yt-dlp", output)

    def test_install_keeps_manual_only_dependencies_unresolved(self):
        commands = {
            "gh": {
                "auto": None,
                "manual": "Install GitHub CLI with Homebrew or the official package manager.",
            }
        }
        modules = {}

        status, output, run_mock = self.run_main(
            ["--install"],
            commands=commands,
            modules=modules,
        )

        self.assertEqual(status, 1)
        run_mock.assert_not_called()
        self.assertIn("manual install required for gh", output)
        self.assertIn("still missing command: gh", output)

    def test_install_returns_zero_after_command_becomes_available(self):
        commands = {
            "yt-dlp": {
                "auto": ["pipx", "install", "yt-dlp"],
                "manual": "pipx install yt-dlp",
            }
        }
        modules = {}
        available_commands = {"pipx"}

        def successful_install(command, check=False):
            available_commands.add("yt-dlp")
            return subprocess.CompletedProcess(command, 0)

        status, output, run_mock = self.run_main(
            ["--install"],
            commands=commands,
            modules=modules,
            available_commands=available_commands,
            run=successful_install,
        )

        self.assertEqual(status, 0)
        run_mock.assert_called_once_with(["pipx", "install", "yt-dlp"], check=False)
        self.assertNotIn("still missing command", output)

    def test_install_returns_nonzero_without_running_when_package_manager_is_missing(self):
        commands = {
            "mcporter": {
                "auto": ["npm", "install", "-g", "mcporter"],
                "manual": "npm install -g mcporter",
            }
        }
        modules = {}

        status, output, run_mock = self.run_main(
            ["--install"],
            commands=commands,
            modules=modules,
            run=lambda command, check=False: subprocess.CompletedProcess(command, 0),
        )

        self.assertEqual(status, 1)
        run_mock.assert_not_called()
        self.assertIn("manual install required for mcporter", output)
        self.assertIn("npm install -g mcporter", output)

    def test_install_rechecks_modules_after_successful_install(self):
        commands = {}
        modules = {
            "feedparser": {
                "auto": [self.globals["sys"].executable, "-m", "pip", "install", "feedparser"],
                "manual": "Install feedparser into Linky's Python environment.",
            }
        }
        available_modules = set()

        def successful_install(command, check=False):
            available_modules.add("feedparser")
            return subprocess.CompletedProcess(command, 0)

        with mock.patch.object(self.globals["importlib"], "invalidate_caches") as invalidate_caches:
            status, output, run_mock = self.run_main(
                ["--install"],
                commands=commands,
                modules=modules,
                available_modules=available_modules,
                run=successful_install,
            )

        self.assertEqual(status, 0)
        invalidate_caches.assert_called_once_with()
        run_mock.assert_called_once_with(
            [self.globals["sys"].executable, "-m", "pip", "install", "feedparser"],
            check=False,
        )
        self.assertNotIn("still missing module", output)


if __name__ == "__main__":
    unittest.main()
