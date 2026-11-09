import http.client
import io
import socket
import threading
import time
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from linky import safe_http


class SafeHTTPTests(unittest.TestCase):
    def test_rejects_unsafe_url_forms_before_dns(self):
        bad = ['file:///etc/passwd', 'http://user:pass@example.com/a', 'http://localhost/a',
               'http://127.0.0.1/a', 'http://[::1]/a', 'http://169.254.169.254/a',
               'https://example.com:22/a', 'https://example.com/\r\nX:y',
               'https://example.com\\@127.0.0.1/a', 'https://example.com/%0d%0aX:y',
               'http://2130706433/', 'http://0x7f000001/', 'https://example.com./a']
        with patch('linky.safe_http.socket.getaddrinfo') as dns:
            for url in bad:
                with self.subTest(url=url), self.assertRaises(safe_http.RestrictedURL):
                    safe_http.validate_url(url)
            dns.assert_not_called()

    def test_dns_rejects_any_private_answer(self):
        for address in ['10.0.0.1', '192.168.2.1', '100.64.0.1', '0.0.0.0', '224.0.0.1', '::ffff:127.0.0.1', '2001:db8::1']:
            with self.subTest(address=address), patch('linky.safe_http.socket.getaddrinfo', return_value=[(2, 1, 6, '', ('93.184.216.34', 443)), (2, 1, 6, '', (address, 443))]):
                with self.assertRaises(safe_http.RestrictedURL):
                    safe_http.resolve_public('example.com', 443)

    def test_public_connection_is_pinned_without_second_dns_lookup(self):
        with patch('linky.safe_http.socket.getaddrinfo', return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443))]), patch('linky.safe_http.socket.socket') as sock:
            conn = safe_http.PinnedHTTPConnection('example.com', 443, safe_http.resolve_public('example.com', 443), timeout=5)
            conn.connect()
            sock.return_value.connect.assert_called_once_with(('93.184.216.34', 443))

    def test_redirect_to_private_is_rejected_before_next_request(self):
        response = FakeResponse(302, b'', {'Location': 'http://127.0.0.1/secret'})
        with patch.object(safe_http.SafeHTTPClient, '_request', return_value=response) as request:
            with self.assertRaises(safe_http.RestrictedURL):
                safe_http.SafeHTTPClient().open('https://example.com/a')
            self.assertEqual(request.call_count, 1)
            self.assertTrue(response.closed)

    def test_downgrade_and_redirect_limit(self):
        for target in ['http://example.com/b', 'https://example.com/b']:
            with patch.object(safe_http.SafeHTTPClient, '_request', return_value=FakeResponse(302, b'', {'Location': target})):
                with self.assertRaises(safe_http.RestrictedURL):
                    safe_http.SafeHTTPClient(max_redirects=0).open('https://example.com/a')

    def test_dns_resolution_has_bounded_wait(self):
        event = threading.Event()
        def slow_dns(*args, **kwargs):
            event.wait(2)
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443))]
        start = time.monotonic()
        try:
            with patch('linky.safe_http.socket.getaddrinfo', side_effect=slow_dns):
                with self.assertRaises(TimeoutError):
                    safe_http.resolve_public('example.com', 443, timeout=0.03)
        finally:
            event.set()
        self.assertLess(time.monotonic() - start, 0.5)

    def test_deadline_closes_connection_even_during_header_read(self):
        with patch('linky.safe_http.socket.socket') as sock:
            conn = safe_http.PinnedHTTPConnection('example.com', 80, (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 80)), timeout=5, deadline=time.monotonic()+0.03)
            conn.connect()
            time.sleep(0.08)
            sock.return_value.shutdown.assert_called()
            sock.return_value.close.assert_called()
            conn.close()

    def test_deadline_interrupts_dripped_chunk_framing_after_headers(self):
        from unittest.mock import MagicMock
        client, server = socket.socketpair()
        wrapper = MagicMock(wraps=client)
        wrapper.connect.side_effect = lambda address: None
        wrapper.makefile.side_effect = client.makefile
        conn = safe_http.PinnedHTTPConnection('example.com', 80, (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 80)), timeout=0.2, deadline=time.monotonic()+0.12)
        def serve():
            try:
                server.recv(4096)
                server.sendall(b'HTTP/1.1 200 OK\r\nConnection: close\r\nTransfer-Encoding: chunked\r\n\r\n')
                for byte in b'1;extension=' + b'x'*100 + b'\r\na\r\n0\r\n\r\n':
                    server.sendall(bytes([byte]))
                    time.sleep(0.01)
            except OSError:
                pass
            finally:
                server.close()
        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        start = time.monotonic()
        try:
            with patch('linky.safe_http.socket.socket', return_value=wrapper):
                conn.request('GET', '/')
                response = conn.getresponse()
            with self.assertRaises((OSError, http.client.HTTPException)):
                response.read1(1024)
            self.assertLess(time.monotonic()-start, 0.5)
        finally:
            conn.close()
            client.close()

    def test_tls_watchdog_owns_ssl_socket_before_handshake(self):
        from unittest.mock import MagicMock
        ssl_socket = MagicMock()
        context = MagicMock()
        context.wrap_socket.return_value = ssl_socket
        conn = safe_http.PinnedHTTPSConnection('example.com', 443, (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443)), timeout=1, deadline=time.monotonic()+0.1)
        def handshake():
            self.assertIs(conn.deadline_socket, ssl_socket)
        ssl_socket.do_handshake.side_effect = handshake
        try:
            with patch('linky.safe_http.socket.socket'), patch('linky.safe_http.ssl.create_default_context', return_value=context):
                conn.connect()
            self.assertFalse(context.wrap_socket.call_args.kwargs['do_handshake_on_connect'])
            ssl_socket.do_handshake.assert_called_once()
        finally:
            conn.finish()

    def test_redacts_query_fragment_userinfo_in_provenance(self):
        self.assertEqual(safe_http.public_url('https://u:p@example.com/a?token=secret#x'), 'https://example.com/a')


class FakeResponse:
    def __init__(self, status=200, body=b'', headers=None, fail=False):
        self.status, self.headers = status, headers or {}
        self.stream = io.BytesIO(body)
        self.closed, self.fail = False, fail
        self.url = 'https://example.com/file'
        self.redirects = []
    def read(self, size=-1):
        data = self.stream.read(size)
        if not data and self.fail:
            raise OSError('connection interrupted')
        return data
    def close(self):
        self.closed = True
    def getheader(self, name, default=None):
        return next((v for k, v in self.headers.items() if k.lower() == name.lower()), default)

if __name__ == '__main__':
    unittest.main()
