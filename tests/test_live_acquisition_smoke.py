import importlib.util
import unittest
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('live_smoke', Path(__file__).with_name('live_acquisition_smoke.py'))
live_smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(live_smoke)


class LiveSmokeSourceTests(unittest.TestCase):
    def test_pr_uses_explicit_head_repository_and_sha_not_merge_head(self):
        head = 'a'*40
        with patch.object(live_smoke.subprocess, 'check_output', side_effect=AssertionError('merge HEAD must not be read')):
            self.assertEqual(live_smoke.public_source({'ACQUISITION_SMOKE_REPOSITORY':'contributor/linky', 'ACQUISITION_SMOKE_REF':head}), ('contributor/linky', head))

    def test_local_run_uses_current_commit(self):
        with patch.object(live_smoke.subprocess, 'check_output', return_value='b'*40+'\n'):
            self.assertEqual(live_smoke.public_source({}), ('imarco/linky', 'b'*40))

    def test_source_metadata_cannot_inject_url_components(self):
        for repo, ref in [('https://evil.test/a','a'*40), ('../linky','a'*40), ('imarco/linky','main?token=x')]:
            with self.subTest(repo=repo, ref=ref), self.assertRaises(ValueError):
                live_smoke.public_source({'ACQUISITION_SMOKE_REPOSITORY':repo,'ACQUISITION_SMOKE_REF':ref})

    def test_fixture_comparison_reads_selected_commit_not_working_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            subprocess.run(['git', '-C', str(root), 'config', 'user.name', 'Test'], check=True)
            subprocess.run(['git', '-C', str(root), 'config', 'user.email', 'test@example.invalid'], check=True)
            fixture = root/'tests/fixtures/acquisition/public.pdf'
            fixture.parent.mkdir(parents=True)
            fixture.write_bytes(b'PR head fixture')
            subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(root), 'commit', '-qm', 'head fixture'], check=True)
            head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
            fixture.write_bytes(b'base change present only in merged tree')
            with patch.object(live_smoke, 'ROOT', root):
                self.assertEqual(live_smoke.fixture_bytes(head, 'public.pdf'), b'PR head fixture')
