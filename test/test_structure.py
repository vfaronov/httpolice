# -*- coding: utf-8; -*-

from httpolice.exchange import Exchange
from httpolice.request import Request
from httpolice.response import Response
from httpolice.structure import (
    CaseInsensitive,
    FieldName,
    HTTPVersion,
    Method,
    Parametrized,
    StatusCode,
)


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
