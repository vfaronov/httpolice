# -*- coding: utf-8; -*-

import unittest

from six.moves import StringIO

from httpolice.exchange import check_exchange
from httpolice.framing1 import parse_streams
from httpolice.known import cache
from httpolice.reports import html_report, text_report
from httpolice.structure import (
    CacheDirective,
    Parametrized,
    TransferCoding,
    Unavailable,
    http11,
)


class TestRequest(unittest.TestCase):

    @staticmethod
    def parse(inbound, scheme=u'http'):
        outbound = (b'HTTP/1.1 400 Bad Request\r\n'
                    b'Date: Thu, 28 Jan 2016 19:30:21 GMT\r\n'
                    b'Content-Length: 0\r\n'
                    b'\r\n') * 10        # Enough to cover all requests
        exchanges = list(parse_streams(inbound, outbound, scheme=scheme))
        for exch in exchanges:
            check_exchange(exch)
        text_report(exchanges, StringIO())
        html_report(exchanges, StringIO())
        return [exch.request for exch in exchanges if exch.request]

    def test_parse_requests(self):
        stream = (b'GET /foo/bar/baz?qux=xyzzy HTTP/1.1\r\n'
                  b'Host: example.com\r\n'
                  b'X-Foo: bar,\r\n'
                  b'\t\tbaz\r\n'
                  b'\r\n'
                  b'POST /foo/bar/ HTTP/1.1\r\n'
                  b'Host: example.com\r\n'
                  b'Content-Length: 21\r\n'
                  b'\r\n' +
                  u'Привет мир!\n'.encode('utf-8') +
                  b'OPTIONS * HTTP/1.1\r\n'
                  b'Host: example.com\r\n'
                  b'Content-Length: 0\r\n'
                  b'\r\n')
        [req1, req2, req3] = self.parse(stream)

        self.assertEqual(req1.method, u'GET')
        self.assertEqual(req1.target, u'/foo/bar/baz?qux=xyzzy')
        self.assertEqual(req1.version, http11)
        self.assertEqual(req1.header_entries[0].name, u'Host')
        self.assertEqual(req1.header_entries[0].value, b'example.com')
        self.assertEqual(req1.header_entries[1].name, u'X-Foo')
        self.assertEqual(req1.header_entries[1].value, b'bar, baz')
        self.assertEqual(req1.body, b'')
        self.assertEqual(repr(req1.header_entries[1]), '<HeaderEntry X-Foo>')
        self.assertEqual(repr(req1), '<Request GET>')

        self.assertEqual(req2.method, u'POST')
        self.assertEqual(req2.target, u'/foo/bar/')
        self.assertEqual(req2.header_entries[1].name, u'content-length')
        self.assertEqual(req2.headers.content_length.value, 21)
        self.assertEqual(req2.headers.content_length.is_present, True)
        self.assertEqual(repr(req2.headers.content_length),
                         '<SingleHeaderView Content-Length>')
        self.assertEqual(
            req2.body,
            b'\xd0\x9f\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82 '
            b'\xd0\xbc\xd0\xb8\xd1\x80!\n')

        self.assertEqual(req3.method, u'OPTIONS')
        self.assertEqual(req3.target, u'*')
        self.assertEqual(req3.body, b'')

    def test_unparseable_framing(self):
        self.assertEqual(self.parse(b'GET ...'), [])

    def test_unparseable_body(self):
        stream = (b'POST / HTTP/1.1\r\n'
                  b'Host: example.com\r\n'
                  b'Content-Length: 90\r\n'
                  b'\r\n'
                  b'wololo')
        [req1] = self.parse(stream)
        self.assertEqual(req1.method, u'POST')
        self.assertEqual(req1.headers.content_length.value, 90)
        self.assertIs(req1.body, Unavailable)

    def test_unparseable_content_length(self):
        stream = (b'POST / HTTP/1.1\r\n'
                  b'Host: example.com\r\n'
                  b'Content-Length: 4 5 6\r\n'
                  b'\r\n'
                  b'quux')
        [req1] = self.parse(stream)
        self.assertIs(req1.body, Unavailable)

    def test_unparseable_following_parseable(self):
        stream = (b'GET / HTTP/1.1\r\n'
                  b'Host: example.com\r\n'
                  b'\r\n'
                  b'GET /\r\n'
                  b'Host: example.com\r\n')
        [req1] = self.parse(stream)
        self.assertEqual(req1.method, u'GET')
        self.assertEqual(req1.body, b'')

    def test_funny_headers(self):
        stream = (b'GET / HTTP/1.1\r\n'
                  b'Host: example.com\r\n'
                  b'Foo:    \r\n'
                  b'     \r\n'
                  b'  bar baz qux\r\n'
                  b'    xyzzy\r\n'
                  b' \r\n'
                  b'Bar:\r\n'
                  b' \r\n'
                  b' wololo\t\t\r\n'
                  b'Baz:\r\n'
                  b'\r\n')
        [req1] = self.parse(stream)
        # According to my reading of the spec (which may be wrong),
        # every ``obs-fold`` becomes one space,
        # and these spaces are *not* stripped
        # from either end of the resulting ``field-value``.
        self.assertEqual(req1.header_entries[1].value,
                         b'  bar baz qux xyzzy ')
        self.assertEqual(req1.header_entries[2].value, b'  wololo')
        self.assertEqual(req1.header_entries[3].value, b'')

    def test_transfer_codings(self):
        stream = (b'POST / HTTP/1.1\r\n'
                  b'Host: example.com\r\n'
                  b'Transfer-Encoding: foo\r\n'
                  b'Transfer-Encoding:   ,\r\n'
                  b'Transfer-Encoding: gzip, chunked\r\n'
                  b'\r\n'
                  b'0\r\n'
                  b'\r\n')
        [req] = self.parse(stream)
        self.assertIs(req.body, Unavailable)
        self.assertEqual(list(req.headers.transfer_encoding),
                         [Parametrized(u'foo', []),
                          Unavailable,
                          Parametrized(u'gzip', []),
                          Parametrized(u'chunked', [])])
        self.assertEqual(req.annotations[(False, 1)],
                         [TransferCoding(u'foo')])
        self.assertNotIn((False, 2), req.annotations)
        self.assertEqual(req.annotations[(False, 3)],
                         [TransferCoding(u'gzip'), b', ',
                          TransferCoding(u'chunked')])

    def test_parse_chunked(self):
        stream = (b'POST / HTTP/1.1\r\n'
                  b'Transfer-Encoding: ,, chunked,\r\n'
                  b'\r\n'
                  b'1c\r\n'
                  b'foo bar foo bar foo bar baz \r\n'
                  b'5;ext1=value1;ext2="value2 value3"\r\n'
                  b'xyzzy\r\n'
                  b'0\r\n'
                  b'X-Result: okay\r\n'
                  b'\r\n')
        [req1] = self.parse(stream)
        self.assertEqual(req1.method, u'POST')
        self.assertEqual(len(req1.headers.transfer_encoding), 1)
        self.assertEqual(req1.headers.transfer_encoding[0].item, u'chunked')
        self.assertEqual(req1.body, b'foo bar foo bar foo bar baz xyzzy')
        self.assertEqual(len(req1.header_entries), 1)
        self.assertEqual(len(req1.trailer_entries), 1)
        self.assertEqual(req1.trailer_entries[0].name, u'x-result')
        self.assertEqual(req1.trailer_entries[0].value, b'okay')
        self.assertEqual(req1.headers[u'X-Result'].value, b'okay')

    def test_parse_chunked_empty(self):
        stream = (b'POST / HTTP/1.1\r\n'
                  b'Host: example.com\r\n'
                  b'Transfer-encoding:  chunked\r\n'
                  b'\r\n'
                  b'0\r\n'
                  b'\r\n')
        [req] = self.parse(stream)
        self.assertEqual(req.body, b'')

    def test_parse_chunked_no_chunks(self):
        stream = (b'POST / HTTP/1.1\r\n'
                  b'Host: example.com\r\n'
                  b'Transfer-encoding:  chunked\r\n'
                  b'\r\n'
                  b'GET / HTTP/1.1\r\n'
                  b'Host: example.com\r\n'
                  b'\r\n')
        [req] = self.parse(stream)
        self.assertIs(req.body, Unavailable)

    def test_effective_uri_1(self):
        stream = (b'GET /pub/WWW/TheProject.html HTTP/1.1\r\n'
                  b'Host: www.example.org:8080\r\n'
                  b'\r\n')
        [req] = self.parse(stream)
        self.assertEqual(
            req.effective_uri,
            u'http://www.example.org:8080/pub/WWW/TheProject.html')

    def test_effective_uri_2(self):
        stream = (b'GET /pub/WWW/TheProject.html HTTP/1.0\r\n'
                  b'\r\n')
        [req] = self.parse(stream)
        self.assertIs(req.effective_uri, None)

    def test_effective_uri_3(self):
        stream = (b'OPTIONS * HTTP/1.1\r\n'
                  b'Host: www.example.org\r\n'
                  b'\r\n')
        [req] = self.parse(stream, scheme=u'https')
        self.assertEqual(req.effective_uri, u'https://www.example.org')

    def test_effective_uri_4(self):
        stream = (b'GET myproto://www.example.org/index.html HTTP/1.1\r\n'
                  b'Host: www.example.org\r\n'
                  b'\r\n')
        [req] = self.parse(stream)
        self.assertEqual(req.effective_uri,
                         u'myproto://www.example.org/index.html')

    def test_cache_control(self):
        stream = (b'GET / HTTP/1.1\r\n'
                  b'Host: example.com\r\n'
                  b'Cache-Control: max-age="3600", max-stale=60,\r\n'
                  b'Cache-Control: "foo bar"\r\n'
                  b'Via: 1.1 baz\r\n'
                  b'Cache-Control: qux="xyzzy 123", ,no-transform, abcde\r\n'
                  b'Cache-Control: min-fresh, no-store=yes\r\n'
                  b'Pragma: no-cache, foo, bar=baz, qux="xyzzy"\r\n'
                  b'Pragma: no-cache=krekfewhrfk\r\n'
                  b'\r\n')
        [req] = self.parse(stream)
        self.assertEqual(req.headers.cache_control.value,
                         [Parametrized(cache.max_age, 3600),
                          Parametrized(cache.max_stale, 60),
                          Unavailable,
                          Parametrized(CacheDirective(u'qux'), u'xyzzy 123'),
                          Parametrized(cache.no_transform, None),
                          Parametrized(CacheDirective(u'abcde'), None),
                          Parametrized(cache.min_fresh, Unavailable),
                          Parametrized(cache.no_store, None)])
        self.assertEqual(req.headers.pragma.value,
                         [u'no-cache',
                          (u'foo', None),
                          (u'bar', u'baz'),
                          (u'qux', u'xyzzy'),
                          Unavailable])

        self.assertIn(cache.max_age, req.headers.cache_control)
        self.assertEqual(req.headers.cache_control.max_age, 3600)

        self.assertIn(cache.max_stale, req.headers.cache_control)
        self.assertEqual(req.headers.cache_control.max_stale, 60)

        self.assertEqual(
            req.headers.cache_control[CacheDirective(u'qux')],
            u'xyzzy 123')

        self.assertIn(cache.no_transform, req.headers.cache_control)
        self.assertEqual(req.headers.cache_control.no_transform, True)

        self.assertEqual(
            req.headers.cache_control[CacheDirective(u'abcde')],
            True)

        self.assertIs(req.headers.cache_control.no_cache, None)

        self.assertIn(cache.min_fresh, req.headers.cache_control)
        self.assertIs(req.headers.cache_control.min_fresh, Unavailable)

        self.assertIn(cache.no_store, req.headers.cache_control)
        self.assertEqual(req.headers.cache_control.no_store, True)

        self.assertNotIn(cache.only_if_cached, req.headers.cache_control)
