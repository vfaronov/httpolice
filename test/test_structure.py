# -*- coding: utf-8; -*-

import unittest

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


class TestStructure(unittest.TestCase):

    def test_common_structures(self):
        self.assertEqual(CaseInsensitive(u'foo'), CaseInsensitive(u'Foo'))
        self.assertNotEqual(CaseInsensitive(u'foo'), CaseInsensitive(u'bar'))
        self.assertEqual(CaseInsensitive(u'foo'), u'Foo')
        self.assertNotEqual(CaseInsensitive(u'foo'), u'bar')
        self.assertEqual(Parametrized(CaseInsensitive(u'foo'), []),
                         CaseInsensitive(u'Foo'))
        self.assertEqual(
            Parametrized(CaseInsensitive(u'foo'), [(u'bar', u'qux')]),
            u'Foo')
        self.assertNotEqual(
            Parametrized(CaseInsensitive(u'foo'), [(u'bar', u'qux')]),
            u'bar')
        self.assertEqual(
            Parametrized(CaseInsensitive(u'foo'), [(u'bar', u'qux')]),
            Parametrized(CaseInsensitive(u'Foo'), [(u'bar', u'qux')]))
        self.assertNotEqual(
            Parametrized(CaseInsensitive(u'foo'), [(u'bar', u'qux')]),
            Parametrized(CaseInsensitive(u'foo'), [(u'bar', u'xyzzy')]))
        self.assertNotEqual(
            Parametrized(u'foo', [(u'bar', u'qux')]),
            Parametrized(u'foo', [(u'bar', u'xyzzy')]))
        self.assertNotEqual(
            Parametrized(CaseInsensitive(u'foo'), [(u'bar', u'qux')]),
            Parametrized(CaseInsensitive(u'bar'), [(u'bar', u'qux')]))

    def test_construct_exchange(self):
        req = Request(u'http',
                      u'GET', u'/', u'HTTP/1.1',
                      [(u'Host', b'example.com')],
                      None)
        self.assertEqual(repr(req), '<Request GET>')
        resp1 = Response(u'HTTP/1.1', 123, u'Please wait', [], None)
        self.assertEqual(repr(resp1), '<Response 123>')
        resp2 = Response(u'HTTP/1.1', 200, u'OK',
                         [(u'Content-Length', b'14')],
                         b'Hello world!\r\n',
                         None)
        exch = Exchange(req, [resp1, resp2])
        self.assertEqual(repr(exch),
                         'Exchange(<Request GET>, '
                         '[<Response 123>, <Response 200>])')
        self.assertTrue(isinstance(exch.request.method, Method))
        self.assertTrue(isinstance(exch.request.version, HTTPVersion))
        self.assertTrue(isinstance(exch.request.header_entries[0].name,
                                   FieldName))
        self.assertTrue(isinstance(exch.responses[0].version, HTTPVersion))
        self.assertTrue(isinstance(exch.responses[0].status, StatusCode))
        self.assertTrue(isinstance(exch.responses[1].header_entries[0].name,
                                   FieldName))

