"""Credential-free HTTP with public-address validation and DNS-pinned sockets.

This module deliberately does not use urllib proxy handlers, netrc, cookies,
requests sessions, gh or browser state. Redirects are validated before opening.
"""
from __future__ import annotations

import http.client
import ipaddress
import re
import queue
import threading
import time
import socket
import ssl
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit


class RestrictedURL(ValueError):
    """The request would cross the public-resource boundary."""


def public_url(url: str) -> str:
    """Persist no credentials, query tokens, or fragments in provenance."""
    try:
        parts = urlsplit(url)
        host = parts.hostname or ''
        if ':' in host:
            host = f'[{host}]'
        if parts.port:
            host += f':{parts.port}'
        return urlunsplit((parts.scheme, host, parts.path, '', ''))
    except ValueError:
        return '[invalid URL]'


def validate_url(url: str):
    if not isinstance(url, str) or len(url) > 8192 or any(c in url for c in ('\\', '\r', '\n', '\t')):
        raise RestrictedURL('invalid URL characters or length')
    if re.search(r'[\x00-\x20\x7f]', url) or re.search(r'[\x00-\x1f\x7f]', unquote(url)):
        raise RestrictedURL('URL contains control characters or spaces')
    try:
        parts = urlsplit(url)
        host, port = parts.hostname, parts.port
    except ValueError as exc:
        raise RestrictedURL('malformed URL') from exc
    if parts.scheme not in {'http', 'https'} or not host or parts.username is not None or parts.password is not None:
        raise RestrictedURL('only public HTTP(S) URLs without credentials are allowed')
    if port not in {None, 80, 443}:
        raise RestrictedURL('only standard HTTP(S) ports are allowed')
    if host.endswith('.') or '%' in host or host.lower() == 'localhost' or host.lower().endswith(('.localhost', '.local', '.internal', '.test', '.invalid', '.onion')):
        raise RestrictedURL('local or non-public hostname')
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        # Reject alternate IPv4 spellings and malformed names before resolver use.
        if '.' not in host or not re.fullmatch(r'[A-Za-z0-9.-]+', host) or re.fullmatch(r'[0-9a-fA-FxX.]+', host):
            raise RestrictedURL('ambiguous or invalid hostname')
        if any(not label or len(label) > 63 or label.startswith('-') or label.endswith('-') for label in host.split('.')):
            raise RestrictedURL('invalid hostname')
    else:
        _check_address(address)
    return parts


def _check_address(address):
    if not address.is_global or address.is_multicast or address.is_unspecified or address.is_reserved or address.is_loopback or address.is_link_local:
        raise RestrictedURL('non-public network address')
    if isinstance(address, ipaddress.IPv6Address) and (address.ipv4_mapped or address.sixtofour or address.teredo):
        raise RestrictedURL('IPv6 transition addresses are not allowed')


_DNS_SLOTS = threading.BoundedSemaphore(4)


def resolve_public(host: str, port: int, *, timeout=20):
    # libc DNS has no portable cancellation API. Limit concurrent resolver work,
    # wait only to the deadline, and use daemon workers so stalled DNS cannot
    # keep the CLI alive. A timed-out lookup can never initiate a connection.
    if timeout <= 0 or not _DNS_SLOTS.acquire(blocking=False):
        raise TimeoutError('DNS deadline or resolver concurrency limit reached')
    results = queue.Queue(maxsize=1)
    def resolve():
        try:
            results.put((socket.getaddrinfo(host, port, type=socket.SOCK_STREAM), None))
        except Exception as exc:
            results.put((None, exc))
        finally:
            _DNS_SLOTS.release()
    threading.Thread(target=resolve, daemon=True).start()
    try:
        answers, error = results.get(timeout=timeout)
    except queue.Empty as exc:
        raise TimeoutError('DNS resolution deadline reached') from exc
    if error:
        raise error
    if not answers:
        raise OSError('DNS returned no addresses')
    for family, socktype, proto, canonname, sockaddr in answers:
        _check_address(ipaddress.ip_address(sockaddr[0]))
    # Pin one validated address. No unvalidated re-resolution or automatic fallback.
    return answers[0]


class PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host, port, address, *, timeout, deadline=None):
        super().__init__(host, port, timeout=timeout)
        self.address = address
        self.deadline = deadline or (time.monotonic() + timeout)
        self.watchdog = None
        self.deadline_socket = None

    def connect(self):
        family, socktype, proto, _, sockaddr = self.address
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('request deadline reached')
        sock = socket.socket(family, socktype, proto)
        self.sock = self.deadline_socket = sock
        self.watchdog = threading.Timer(remaining, self._expire)
        self.watchdog.daemon = True
        self.watchdog.start()
        try:
            sock.settimeout(min(self.timeout, remaining))
            sock.connect(sockaddr)
        except BaseException:
            sock.close()
            raise
        self.sock = sock

    def _expire(self):
        # shutdown interrupts blocked header/chunk-framing reads, including
        # responses that drip bytes more frequently than the socket timeout.
        sock = self.deadline_socket
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()

    def finish(self):
        if self.watchdog:
            self.watchdog.cancel()
        super().close()
        if self.deadline_socket is not None:
            self.deadline_socket.close()


class PinnedHTTPSConnection(PinnedHTTPConnection):
    def connect(self):
        super().connect()
        try:
            # Certificate validation and SNI use the original hostname, not its IP.
            self.sock = self.deadline_socket = ssl.create_default_context().wrap_socket(self.sock, server_hostname=self.host, do_handshake_on_connect=False)
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('TLS handshake deadline reached')
            self.sock.settimeout(min(self.timeout, remaining))
            self.sock.do_handshake()
        except BaseException:
            self.sock.close()
            raise


class HTTPResponse:
    def __init__(self, connection, response, url):
        self.connection, self.response, self.url = connection, response, url
        self.status = response.status
        self.redirects = []

    def getheader(self, name, default=None):
        return self.response.getheader(name, default)

    def read(self, size=-1):
        # read1 prevents a slow peer from holding one read open indefinitely by
        # delivering one byte per socket timeout interval.
        data = self.response.read1(size)
        if time.monotonic() >= self.connection.deadline:
            raise TimeoutError('whole-request deadline reached')
        return data

    def close(self):
        self.response.close()
        self.connection.finish()


class SafeHTTPClient:
    def __init__(self, *, timeout=20, max_redirects=5, max_seconds=120):
        self.timeout, self.max_redirects, self.max_seconds = timeout, max_redirects, max_seconds
        self.deadline = None

    def _request(self, url):
        parts = validate_url(url)
        port = parts.port or (443 if parts.scheme == 'https' else 80)
        address = resolve_public(parts.hostname, port, timeout=min(self.timeout, self.deadline - time.monotonic()))
        cls = PinnedHTTPSConnection if parts.scheme == 'https' else PinnedHTTPConnection
        conn = cls(parts.hostname, port, address, timeout=self.timeout, deadline=self.deadline)
        try:
            conn.request('GET', urlunsplit(('', '', parts.path or '/', parts.query, '')),
                         headers={'User-Agent': 'Linky/0.5 public-resource-archiver', 'Accept-Encoding': 'identity', 'Accept': '*/*', 'Connection': 'close'})
            return HTTPResponse(conn, conn.getresponse(), url)
        except BaseException:
            conn.finish()
            raise

    def open(self, url):
        self.deadline = time.monotonic() + self.max_seconds
        redirects = []
        current = url
        while True:
            validate_url(current)
            response = self._request(current)
            if response.status not in {301, 302, 303, 307, 308}:
                response.url, response.redirects = current, redirects
                return response
            location = response.getheader('Location')
            response.close()
            if not location or len(redirects) >= self.max_redirects:
                raise RestrictedURL('missing Location or redirect limit reached')
            target = urljoin(current, location)
            validate_url(target)
            if urlsplit(current).scheme == 'https' and urlsplit(target).scheme != 'https':
                raise RestrictedURL('HTTPS downgrade redirect rejected')
            redirects.append(public_url(current))
            current = target
