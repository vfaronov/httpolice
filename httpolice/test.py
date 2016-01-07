# -*- coding: utf-8; -*-

import unittest

from httpolice import parse, request, syntax, transfer_coding, version
from httpolice.common import CaseInsensitive, Parametrized, Unparseable
from httpolice.transfer_coding import known_codings as tc


class TestCommon(unittest.TestCase):

    def test_data_structures(self):
        self.assertEquals(CaseInsensitive(u'foo'), CaseInsensitive(u'Foo'))
        self.assertNotEquals(CaseInsensitive(u'foo'), CaseInsensitive(u'bar'))
        self.assertEquals(CaseInsensitive(u'foo'), u'Foo')
        self.assertNotEquals(CaseInsensitive(u'foo'), u'bar')
        self.assertEquals(Parametrized(CaseInsensitive(u'foo'), []),
                          CaseInsensitive(u'Foo'))
        self.assertEquals(
            Parametrized(CaseInsensitive(u'foo'), [('bar', 'qux')]),
            u'Foo')
        self.assertNotEquals(
            Parametrized(CaseInsensitive(u'foo'), [('bar', 'qux')]),
            u'bar')
        self.assertEquals(
            Parametrized(CaseInsensitive(u'foo'), [('bar', 'qux')]),
            Parametrized(CaseInsensitive(u'Foo'), [('bar', 'qux')]))
        self.assertNotEquals(
            Parametrized(CaseInsensitive(u'foo'), [('bar', 'qux')]),
            Parametrized(CaseInsensitive(u'foo'), [('bar', 'xyzzy')]))
        self.assertNotEquals(
            Parametrized(CaseInsensitive(u'foo'), [('bar', 'qux')]),
            Parametrized(CaseInsensitive(u'bar'), [('bar', 'qux')]))


class TestSyntax(unittest.TestCase):

    def assertParse(self, parser, text, result):
        self.assertEqual(parser.parse(parse.State(text)), result)

    def assertNoParse(self, parser, text):
        self.assertRaises(parse.ParseError, parser.parse, parse.State(text))

    def test_comma_list(self):
        p = syntax.comma_list(syntax.token) + parse.eof
        self.assertParse(p, '', [])
        self.assertParse(p, ' , ,, , ,', [])
        self.assertParse(p, 'foo', ['foo'])
        self.assertParse(p, 'foo,bar', ['foo', 'bar'])
        self.assertParse(p, 'foo, bar,', ['foo', 'bar'])
        self.assertParse(p, ', ,,,foo, ,bar, baz, ,, ,', ['foo', 'bar', 'baz'])
        self.assertNoParse(p, 'foo,"bar"')
        self.assertNoParse(p, 'foo;bar')

    def test_comma_list1(self):
        p = syntax.comma_list1(syntax.token) + parse.eof
        self.assertNoParse(p, '')
        self.assertNoParse(p, '  \t ')
        self.assertNoParse(p, ' , ,, , ,')
        self.assertParse(p, 'foo', ['foo'])
        self.assertParse(p, 'foo,bar', ['foo', 'bar'])
        self.assertParse(p, 'foo, bar,', ['foo', 'bar'])
        self.assertParse(p, ', ,,,foo, ,bar, baz, ,, ,', ['foo', 'bar', 'baz'])
        self.assertNoParse(p, 'foo,"bar"')
        self.assertNoParse(p, 'foo;bar')

    def test_transfer_coding(self):
        p = syntax.transfer_coding + parse.eof
        self.assertParse(p, 'chunked', Parametrized(tc.chunked, []))
        self.assertParse(p, 'foo',
                         Parametrized(transfer_coding.TransferCoding(u'foo'),
                                      []))
        self.assertParse(p, 'foo ; bar = baz ; qux = "\\"xyzzy\\""',
                         Parametrized(transfer_coding.TransferCoding(u'foo'),
                                      [(u'bar', u'baz'),
                                       (u'qux', u'"xyzzy"')]))
        self.assertNoParse(p, '')
        self.assertNoParse(p, 'foo;???')
        self.assertNoParse(p, 'foo;"bar"="baz"')


class TestRequest(unittest.TestCase):

    def test_parse_requests(self):
        stream = ('GET /foo/bar/baz?qux=xyzzy HTTP/1.1\r\n'
                  'Host: example.com\r\n'
                  'X-Foo: bar,\r\n'
                  '\t\tbaz\r\n'
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
        [req1, req2, req3] = request.parse_stream(stream)

        self.assertEquals(req1.method, u'GET')
        self.assertEquals(req1.target, u'/foo/bar/baz?qux=xyzzy')
        self.assertEquals(req1.version, version.http11)
        self.assertEquals(req1.header_entries[0].name, u'Host')
        self.assertEquals(req1.header_entries[0].value, 'example.com')
        self.assertEquals(req1.header_entries[1].name, u'X-Foo')
        self.assertEquals(req1.header_entries[1].value, 'bar, baz')

        self.assertEquals(req2.method, u'POST')
        self.assertEquals(req2.target, u'/foo/bar/')
        self.assertEquals(req2.header_entries[1].name, u'content-length')
        self.assertEquals(req2.headers.content_length.value, 21)
        self.assertEquals(req2.headers.content_length.is_present, True)
        self.assertEquals(req2.body, 'Привет мир!\n')

        self.assertEquals(req3.method, u'OPTIONS')
        self.assertEquals(req3.target, u'*')

    def test_unparseable_framing(self):
        [req1] = request.parse_stream('GET ...')
        self.assert_(req1 is Unparseable)

    def test_unparseable_body(self):
        stream = ('POST / HTTP/1.1\r\n'
                  'Host: example.com\r\n'
                  'Content-Length: 90\r\n'
                  '\r\n'
                  'wololo')
        [req1] = request.parse_stream(stream)
        self.assertEqual(req1.method, u'POST')
        self.assertEqual(req1.headers.content_length.value, 90)
        self.assert_(req1.body is Unparseable)

    def test_unparseable_content_length(self):
        stream = ('POST / HTTP/1.1\r\n'
                  'Host: example.com\r\n'
                  'Content-Length: 4 5 6\r\n'
                  '\r\n'
                  'quux')
        [req1] = request.parse_stream(stream)
        self.assert_(req1.body is Unparseable)

    def test_unparseable_following_parseable(self):
        stream = ('GET / HTTP/1.1\r\n'
                  'Host: example.com\r\n'
                  '\r\n'
                  'GET /\r\n'
                  'Host: example.com\r\n')
        [req1, req2] = request.parse_stream(stream)
        self.assertEqual(req1.method, u'GET')
        self.assertEqual(req1.body, '')
        self.assert_(req2 is Unparseable)

    def test_transfer_codings(self):
        stream = ('POST / HTTP/1.1\r\n'
                  'Host: example.com\r\n'
                  'Transfer-Encoding: foo\r\n'
                  'Transfer-Encoding:   ,\r\n'
                  'Transfer-Encoding: gzip, chunked\r\n'
                  '\r\n'
                  '0\r\n'
                  '\r\n')
        [req] = request.parse_stream(stream)
        self.assert_(req.body is Unparseable)
        self.assertEqual(list(req.headers.transfer_encoding),
                         [Parametrized(u'foo', []),
                          Parametrized(u'gzip', []),
                          Parametrized(u'chunked', [])])

    def test_parse_chunked(self):
        stream = ('POST / HTTP/1.1\r\n'
                  'Transfer-Encoding: ,, chunked,\r\n'
                  '\r\n'
                  '1c\r\n'
                  'foo bar foo bar foo bar baz \r\n'
                  '5;ext1=value1;ext2="value2 value3"\r\n'
                  'xyzzy\r\n'
                  '0\r\n'
                  'X-Result: okay\r\n'
                  '\r\n')
        [req1] = request.parse_stream(stream)
        self.assertEqual(req1.method, u'POST')
        self.assertEqual(len(req1.headers.transfer_encoding), 1)
        self.assertEqual(req1.headers.transfer_encoding[0].item, u'chunked')
        self.assertEqual(req1.body, 'foo bar foo bar foo bar baz xyzzy')
        self.assertEqual(len(req1.header_entries), 1)
        self.assertEqual(len(req1.trailer_entries), 1)
        self.assertEqual(req1.trailer_entries[0].name, u'x-result')
        self.assertEqual(req1.trailer_entries[0].value, 'okay')
        self.assertEqual(req1.headers[u'X-Result'].value, 'okay')

    def test_parse_chunked_empty(self):
        stream = ('POST / HTTP/1.1\r\n'
                  'Host: example.com\r\n'
                  'Transfer-encoding:  chunked\r\n'
                  '\r\n'
                  '0\r\n'
                  '\r\n')
        [req] = request.parse_stream(stream)
        self.assertEqual(req.body, '')

    def test_parse_chunked_no_chunks(self):
        stream = ('POST / HTTP/1.1\r\n'
                  'Host: example.com\r\n'
                  'Transfer-encoding:  chunked\r\n'
                  '\r\n'
                  'GET / HTTP/1.1\r\n'
                  'Host: example.com\r\n'
                  '\r\n')
        [req] = request.parse_stream(stream)
        self.assert_(req.body is Unparseable)


if __name__ == '__main__':
    unittest.main()
