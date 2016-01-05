# -*- coding: utf-8; -*-

import unittest

from httpolice import request, version
from httpolice.common import Unparseable


class Test(unittest.TestCase):

    def test_parse_requests(self):
        stream = ('GET /foo/bar/baz?qux=xyzzy HTTP/1.1\r\n'
                  'Host: example.com\r\n'
                  '\r\n'
                  'POST /foo/bar/ HTTP/1.1\r\n'
                  'Host: example.com\r\n'
                  'Content-Length: 21\r\n'
                  '\r\n'
                  'Привет мир!\n'
                  'OPTIONS * HTTP/1.1\r\n'
                  'Host: example.com\r\n'
                  'Content-Length: 0\r\n'
                  '\r\n')
        [req1, req2, req3] = request.parse_stream(stream, report=None)

        self.assertEquals(req1.method, u'GET')
        self.assertEquals(req1.target, u'/foo/bar/baz?qux=xyzzy')
        self.assertEquals(req1.version, version.http11)
        self.assertEquals(req1.header_entries[0].name, 'Host')
        self.assertEquals(req1.header_entries[0].value, 'example.com')

        self.assertEquals(req2.method, u'POST')
        self.assertEquals(req2.target, u'/foo/bar/')
        self.assertEquals(req2.header_entries[1].name, u'content-length')
        self.assertEquals(req2.headers.content_length.value, 21)
        self.assertEquals(req2.headers.content_length.is_present, True)
        self.assertEquals(req2.body, 'Привет мир!\n')

        self.assertEquals(req3.method, u'OPTIONS')
        self.assertEquals(req3.target, u'*')

    def test_unparseable_framing(self):
        [req1] = request.parse_stream('GET ...', report=None)
        self.assert_(req1 is Unparseable)

    def test_unparseable_body(self):
        stream = ('POST / HTTP/1.1\r\n'
                  'Content-Length: 90\r\n'
                  '\r\n'
                  'wololo')
        [req1] = request.parse_stream(stream, report=None)
        self.assertEqual(req1.method, u'POST')
        self.assertEqual(req1.headers.content_length.value, 90)
        self.assert_(req1.body is Unparseable)
