# -*- coding: utf-8; -*-

import six

from httpolice.exchange import check_exchange
from httpolice.framing1 import parse_streams
from httpolice.known import cache
from httpolice.reports import html_report, text_report
from httpolice.structure import (
    MultiDict,
    Parametrized,
    TransferCoding,
    Unavailable,
    http11,
)


def go(inbound, scheme=u'http'):
    outbound = (b'HTTP/1.1 400 Bad Request\r\n'
                b'Date: Thu, 28 Jan 2016 19:30:21 GMT\r\n'
                b'Content-Length: 0\r\n'
                b'\r\n') * 10        # Enough to cover all requests
    exchanges = list(parse_streams(inbound, outbound, scheme=scheme))
    for exch in exchanges:
        check_exchange(exch)
    text_report(exchanges, six.BytesIO())
    html_report(exchanges, six.BytesIO())
    return [exch.request for exch in exchanges if exch.request]


def test_parse_requests():
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
    [req1, req2, req3] = go(stream)

    assert req1.method == u'GET'
    assert req1.target == u'/foo/bar/baz?qux=xyzzy'
    assert req1.version == http11
    assert req1.header_entries[0].name == u'Host'
    assert req1.header_entries[0].value == b'example.com'
    assert req1.header_entries[1].name == u'X-Foo'
    assert req1.header_entries[1].value == b'bar, baz'
    assert req1.body == b''
    assert repr(req1.header_entries[1]) == '<HeaderEntry X-Foo>'
    assert repr(req1) == '<Request GET>'

    assert req2.method == u'POST'
    assert req2.target == u'/foo/bar/'
    assert req2.header_entries[1].name == u'content-length'
    assert req2.headers.content_length.value == 21
    assert req2.headers.content_length.is_present
    assert repr(req2.headers.content_length) == \
        '<SingleHeaderView Content-Length>'
    assert req2.body == (b'\xd0\x9f\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82 '
                         b'\xd0\xbc\xd0\xb8\xd1\x80!\n')

    assert req3.method == u'OPTIONS'
    assert req3.target == u'*'
    assert req3.body == b''


def test_unparseable_framing():
    assert go(b'GET ...') == []


def test_unparseable_body():
    stream = (b'POST / HTTP/1.1\r\n'
              b'Host: example.com\r\n'
              b'Content-Length: 90\r\n'
              b'\r\n'
              b'wololo')
    [req1] = go(stream)
    assert req1.method == u'POST'
    assert req1.headers.content_length.value == 90
    assert req1.body is Unavailable


def test_unparseable_content_length():
    stream = (b'POST / HTTP/1.1\r\n'
              b'Host: example.com\r\n'
              b'Content-Length: 4 5 6\r\n'
              b'\r\n'
              b'quux')
    [req1] = go(stream)
    assert req1.body is Unavailable


def test_unparseable_following_parseable():
    stream = (b'GET / HTTP/1.1\r\n'
              b'Host: example.com\r\n'
              b'\r\n'
              b'GET /\r\n'
              b'Host: example.com\r\n')
    [req1] = go(stream)
    assert req1.method == u'GET'
    assert req1.body == b''


def test_funny_headers():
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
    [req1] = go(stream)
    # According to my reading of the spec (which may be wrong),
    # every ``obs-fold`` becomes one space,
    # and these spaces are *not* stripped
    # from either end of the resulting ``field-value``.
    assert req1.header_entries[1].value == b'  bar baz qux xyzzy '
    assert req1.header_entries[2].value == b'  wololo'
    assert req1.header_entries[3].value == b''


def test_transfer_codings():
    stream = (b'POST / HTTP/1.1\r\n'
              b'Host: example.com\r\n'
              b'Transfer-Encoding: foo\r\n'
              b'Transfer-Encoding:   ,\r\n'
              b'Transfer-Encoding: gzip, chunked\r\n'
              b'\r\n'
              b'0\r\n'
              b'\r\n')
    [req] = go(stream)
    assert req.body is Unavailable
    assert list(req.headers.transfer_encoding) == [
        Parametrized(u'foo', MultiDict()),
        Unavailable,
        Parametrized(u'gzip', MultiDict()),
        Parametrized(u'chunked', MultiDict()),
    ]
    assert req.annotations[(False, 1)] == [TransferCoding(u'foo')]
    assert (False, 2) not in req.annotations
    assert req.annotations[(False, 3)] == [TransferCoding(u'gzip'), b', ',
                                           TransferCoding(u'chunked')]


def test_parse_chunked():
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
    [req1] = go(stream)
    assert req1.method == u'POST'
    assert len(req1.headers.transfer_encoding) == 1
    assert req1.headers.transfer_encoding[0].item == u'chunked'
    assert req1.body == b'foo bar foo bar foo bar baz xyzzy'
    assert len(req1.header_entries) == 1
    assert len(req1.trailer_entries) == 1
    assert req1.trailer_entries[0].name == u'x-result'
    assert req1.trailer_entries[0].value == b'okay'
    assert req1.headers[u'X-Result'].value == b'okay'


def test_parse_chunked_empty():
    stream = (b'POST / HTTP/1.1\r\n'
              b'Host: example.com\r\n'
              b'Transfer-encoding:  chunked\r\n'
              b'\r\n'
              b'0\r\n'
              b'\r\n')
    [req] = go(stream)
    assert req.body == b''


def test_parse_chunked_no_chunks():
    stream = (b'POST / HTTP/1.1\r\n'
              b'Host: example.com\r\n'
              b'Transfer-encoding:  chunked\r\n'
              b'\r\n'
              b'GET / HTTP/1.1\r\n'
              b'Host: example.com\r\n'
              b'\r\n')
    [req] = go(stream)
    assert req.body is Unavailable


def test_effective_uri_1():
    stream = (b'GET /pub/WWW/TheProject.html HTTP/1.1\r\n'
              b'Host: www.example.org:8080\r\n'
              b'\r\n')
    [req] = go(stream)
    assert req.effective_uri == \
        u'http://www.example.org:8080/pub/WWW/TheProject.html'


def test_effective_uri_2():
    stream = (b'GET /pub/WWW/TheProject.html HTTP/1.0\r\n'
              b'\r\n')
    [req] = go(stream)
    assert req.effective_uri is None


def test_effective_uri_3():
    stream = (b'OPTIONS * HTTP/1.1\r\n'
              b'Host: www.example.org\r\n'
              b'\r\n')
    [req] = go(stream, scheme=u'https')
    assert req.effective_uri == u'https://www.example.org'


def test_effective_uri_4():
    stream = (b'GET myproto://www.example.org/index.html HTTP/1.1\r\n'
              b'Host: www.example.org\r\n'
              b'\r\n')
    [req] = go(stream)
    assert req.effective_uri == u'myproto://www.example.org/index.html'


def test_cache_control():
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
    [req] = go(stream)

    assert req.headers.cache_control.value == [
        Parametrized(cache.max_age, 3600),
        Parametrized(cache.max_stale, 60),
        Unavailable,
        Parametrized(u'qux', u'xyzzy 123'),
        Parametrized(cache.no_transform, None),
        Parametrized(u'abcde', None),
        Parametrized(cache.min_fresh, Unavailable),
        Parametrized(cache.no_store, None),
    ]

    assert req.headers.pragma.value == [u'no-cache',
                                        (u'foo', None),
                                        (u'bar', u'baz'), (u'qux', u'xyzzy'),
                                        Unavailable]

    assert cache.max_age in req.headers.cache_control
    assert req.headers.cache_control.max_age == 3600

    assert cache.max_stale in req.headers.cache_control
    assert req.headers.cache_control.max_stale == 60

    assert req.headers.cache_control[u'qux'] == u'xyzzy 123'

    assert cache.no_transform in req.headers.cache_control
    assert req.headers.cache_control.no_transform == True

    assert req.headers.cache_control[u'abcde'] == True

    assert req.headers.cache_control.no_cache is None

    assert cache.min_fresh in req.headers.cache_control
    assert req.headers.cache_control.min_fresh is Unavailable

    assert cache.no_store in req.headers.cache_control
    assert req.headers.cache_control.no_store is True

    assert cache.only_if_cached not in req.headers.cache_control
