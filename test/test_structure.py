# -*- coding: utf-8; -*-

from datetime import datetime
import os

from httpolice.exchange import Exchange
from httpolice.inputs.streams import combined_input
from httpolice.known import altsvc, auth, cache, h, hsts, m, pref
from httpolice.request import Request
from httpolice.response import Response
from httpolice.structure import (CaseInsensitive, FieldName, HTTPVersion,
                                 Method, MultiDict, Parametrized, StatusCode,
                                 Unavailable, WarningValue, http10, http11)


def load_from_file(name):
    path = os.path.join(os.path.dirname(__file__), 'combined_data', name)
    return list(combined_input([path]))


def test_common_structures():
    assert CaseInsensitive(u'foo') == CaseInsensitive(u'Foo')
    assert CaseInsensitive(u'foo') != CaseInsensitive(u'bar')
    assert CaseInsensitive(u'foo') == u'Foo'
    assert CaseInsensitive(u'foo') != u'bar'
    assert (Parametrized(CaseInsensitive(u'foo'), []) ==
            CaseInsensitive(u'Foo'))
    assert Parametrized(CaseInsensitive(u'foo'), [(u'bar', u'qux')]) == u'Foo'
    assert Parametrized(CaseInsensitive(u'foo'), [(u'bar', u'qux')]) != u'bar'
    assert (Parametrized(CaseInsensitive(u'foo'), [(u'bar', u'qux')]) ==
            Parametrized(CaseInsensitive(u'Foo'), [(u'bar', u'qux')]))
    assert (Parametrized(CaseInsensitive(u'foo'), [(u'bar', u'qux')]) !=
            Parametrized(CaseInsensitive(u'foo'), [(u'bar', u'xyzzy')]))
    assert (Parametrized(u'foo', [(u'bar', u'qux')]) !=
            Parametrized(u'foo', [(u'bar', u'xyzzy')]))
    assert (Parametrized(CaseInsensitive(u'foo'), [(u'bar', u'qux')]) !=
            Parametrized(CaseInsensitive(u'bar'), [(u'bar', u'qux')]))


def test_construct_exchange():
    req = Request(u'http',
                  u'GET', u'/', u'HTTP/1.1',
                  [(u'Host', b'example.com')],
                  None)
    assert repr(req) == '<Request GET>'
    resp1 = Response(u'HTTP/1.1', 123, u'Please wait', [], None)
    assert repr(resp1) == '<Response 123>'
    resp2 = Response(u'HTTP/1.1', 200, u'OK',
                     [(u'Content-Length', b'14')],
                     b'Hello world!\r\n',
                     None)
    exch = Exchange(req, [resp1, resp2])
    assert repr(exch) == \
        'Exchange(<Request GET>, [<Response 123>, <Response 200>])'
    assert isinstance(exch.request.method, Method)
    assert isinstance(exch.request.version, HTTPVersion)
    assert isinstance(exch.request.header_entries[0].name, FieldName)
    assert isinstance(exch.responses[0].version, HTTPVersion)
    assert isinstance(exch.responses[0].status, StatusCode)
    assert isinstance(exch.responses[1].header_entries[0].name, FieldName)


def test_effective_uri_1():
    req = Request(u'http',
                  m.GET, u'/pub/WWW/TheProject.html', http11,
                  [(h.host, b'www.example.org:8080')],
                  b'')
    assert req.effective_uri == \
        u'http://www.example.org:8080/pub/WWW/TheProject.html'


def test_effective_uri_2():
    req = Request(u'http',
                  m.GET, u'/pub/WWW/TheProject.html', http10,
                  [],
                  b'')
    assert req.effective_uri is None


def test_effective_uri_3():
    req = Request(u'https',
                  m.OPTIONS, u'*', http11,
                  [(h.host, b'www.example.org')],
                  b'')
    assert req.effective_uri == u'https://www.example.org'


def test_effective_uri_4():
    req = Request(u'http',
                  m.GET, u'myproto://www.example.org/index.html', http11,
                  [(h.host, b'www.example.org')],
                  b'')
    assert req.effective_uri == u'myproto://www.example.org/index.html'


def test_cache_control():
    [exch1] = load_from_file('funny_cache_control')
    headers = exch1.request.headers

    assert headers.cache_control.value == [
        Parametrized(cache.max_age, 3600),
        Parametrized(cache.max_stale, 60),
        Unavailable,
        Parametrized(u'qux', u'xyzzy 123'),
        Parametrized(cache.no_transform, None),
        Parametrized(u'abcde', None),
        Parametrized(cache.min_fresh, Unavailable),
        Parametrized(cache.no_store, None),
    ]

    assert headers.pragma.value == [u'no-cache',
                                    (u'foo', None),
                                    (u'bar', u'baz'), (u'qux', u'xyzzy'),
                                    Unavailable]

    assert cache.max_age in headers.cache_control
    assert headers.cache_control.max_age == 3600

    assert cache.max_stale in headers.cache_control
    assert headers.cache_control.max_stale == 60

    assert headers.cache_control[u'qux'] == u'xyzzy 123'

    assert cache.no_transform in headers.cache_control
    assert headers.cache_control.no_transform == True

    assert headers.cache_control[u'abcde'] == True

    assert headers.cache_control.no_cache is None

    assert cache.min_fresh in headers.cache_control
    assert headers.cache_control.min_fresh is Unavailable

    assert cache.no_store in headers.cache_control
    assert headers.cache_control.no_store is True

    assert cache.only_if_cached not in headers.cache_control


def test_warning():
    [exch1] = load_from_file('funny_warning')
    warning = exch1.responses[0].headers.warning
    assert warning.value == [
        WarningValue(123, u'-', u'something', None),
        WarningValue(234, u'[::0]:8080', u'something else',
                     datetime(2016, 1, 28, 8, 22, 4)),
        Unavailable,
        WarningValue(456, u'baz', u'qux', None),
        WarningValue(567, u'-', u'xyzzy', None),
    ]
    assert repr(warning.value[0].code) == 'WarnCode(123)'
    assert 123 in warning
    assert 567 in warning
    assert 199 not in warning


def test_www_authenticate():
    [exch1] = load_from_file('funny_www_authenticate')
    assert exch1.responses[0].headers.www_authenticate.value == [
        Parametrized(u'Basic', MultiDict([(u'realm', u'my "magical" realm')])),
        Parametrized(u'Foo', MultiDict()),
        Parametrized(u'Bar', u'jgfCGSU8u=='),
        Parametrized(u'Baz', MultiDict()),
        Unavailable,
        Parametrized(u'Scheme1',
                     MultiDict([(u'foo', u'bar'), (u'baz', u'qux')])),
        Parametrized(u'Scheme2', MultiDict()),
        Parametrized(u'Newauth',
                     MultiDict([(u'realm', u'apps'), (u'type', u'1'),
                                (u'title', u'Login to "apps"')])),
        Parametrized(auth.basic, MultiDict([(u'realm', u'simple')])),
    ]


def test_hsts():
    [exch1] = load_from_file('funny_hsts.https')
    sts = exch1.responses[0].headers.strict_transport_security
    assert sts.value == [
        Parametrized(hsts.max_age, 15768000),
        Parametrized(hsts.includesubdomains, None),
        Parametrized(hsts.max_age, Unavailable),
        Parametrized(u'fooBar', None),
    ]
    assert sts.max_age == 15768000
    assert sts.includesubdomains == True


def test_alt_svc():
    [exch1] = load_from_file('funny_alt_svc')
    assert exch1.responses[0].headers.alt_svc.value == [
        Parametrized(
            (b'http/1.1', u'foo:443'),
            MultiDict([(altsvc.ma, 3600), (altsvc.persist, True)])
        ),
        Parametrized(
            (b'h2', u':8000'),
            MultiDict([(u'foo', u'bar')])
        ),
    ]


def test_prefer():
    [exch1] = load_from_file('funny_prefer')
    assert exch1.request.headers.prefer.value == [
        Parametrized(
            Parametrized(pref.handling, u'lenient'),
            [
                Parametrized(u'param1', u"this is a parameter to 'handling'!"),
                Parametrized(u'param2', None),
            ]
        ),
        Unavailable,
        Parametrized(Parametrized(pref.wait, 600), []),
        Parametrized(
            Parametrized(u'my-pref', None),
            [
                None, None, Parametrized(u'foo', None),
                None, None, Parametrized(u'bar', None),
            ]
        ),
        Parametrized(Parametrized(pref.respond_async, None), []),
        Parametrized(Parametrized(pref.wait, 0), []),
        Parametrized(Parametrized(pref.return_, Unavailable), []),
    ]
    assert exch1.request.headers.prefer.wait == 600
    assert exch1.request.headers.prefer.respond_async
    assert exch1.request.headers.prefer.return_ is Unavailable
    assert exch1.request.headers.prefer[u'quux'] is None


def test_decode_brotli():
    [exch1] = load_from_file('content_encoding_br')
    assert exch1.responses[0].decoded_body.startswith(b'Lorem ipsum dolor')
