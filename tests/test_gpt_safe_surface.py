"""Behavior checks for the public download boundary.

A previous keyword blacklist rejected explicit negative safety statements such
as 'no cookies'. Documentation vocabulary is not a permission/security check.
These tests constrain runtime behavior; installation still needs its independent
platform security scan.
"""
import ast
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from linky.safe_http import SafeHTTPClient


class GPTSafeSurfaceTests(unittest.TestCase):
    def test_acquisition_has_no_shell_or_credential_discovery_apis(self):
        forbidden_imports = {'subprocess', 'requests', 'netrc', 'keyring', 'http.cookiejar', 'urllib.request'}
        forbidden_attributes = {'environ', 'getenv', 'expanduser', 'home', 'system', 'popen'}
        for relative in ['scripts/linky/acquire.py', 'scripts/linky/safe_http.py']:
            tree = ast.parse((ROOT / relative).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertFalse(forbidden_imports.intersection(a.name for a in node.names), relative)
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn(node.module, forbidden_imports, relative)
                if isinstance(node, ast.Attribute):
                    self.assertNotIn(node.attr, forbidden_attributes, relative)

    def test_http_request_does_not_inherit_proxy_or_auth_environment(self):
        conn = MagicMock()
        conn.getresponse.return_value.status = 200
        with patch.dict(os.environ, {'HTTPS_PROXY':'http://127.0.0.1:8888', 'GH_TOKEN':'secret', 'NETRC':'/private/auth'}), patch('linky.safe_http.resolve_public', return_value=(2,1,6,'',('93.184.216.34',443))), patch('linky.safe_http.PinnedHTTPSConnection', return_value=conn):
            response = SafeHTTPClient().open('https://example.com/file')
            response.close()
        headers = conn.request.call_args.kwargs['headers']
        self.assertEqual(set(headers), {'User-Agent', 'Accept-Encoding', 'Accept', 'Connection'})
        self.assertNotIn('secret', str(conn.request.call_args))
        self.assertEqual(conn.request.call_args.args[:2], ('GET', '/file'))

    def test_download_skill_contract_is_explicit(self):
        skill = (ROOT / 'SKILL.md').read_text()
        self.assertIn('授权阅读边界', skill)
        self.assertIn('references/gpt-safe-contract.md', skill)


if __name__ == '__main__':
    unittest.main()
