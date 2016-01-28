# -*- coding: utf-8; -*-

from cStringIO import StringIO
from datetime import datetime
import os
import unittest

from httpolice import HTMLReport, TextReport, analyze_exchange, analyze_streams
from httpolice import parse
from httpolice.known import cache, cc, m, media, tc, unit
from httpolice.notice import notices
from httpolice.report import render_notice_examples
from httpolice.structure import (
    CacheDirective,
    CaseInsensitive,
    ContentCoding,
    ContentRange,
    HTTPVersion,
    FieldName,
    LanguageTag,
    Method,
    MediaType,
    Parametrized,
    ProductName,
    RangeSpecifier,
    RangeUnit,
    Request,
    Response,
    StatusCode,
    TransferCoding,
    Unparseable,
    Versioned,
    WarnCode,
    WarningValue,
    http11,
)
from httpolice.syntax import rfc3986, rfc7230, rfc7231, rfc7233


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

    def assertParse(self, parser, text, result=None):
        r = parser.parse(parse.State(text))
        if result is not None:
            self.assertEqual(r, result)

    def assertNoParse(self, parser, text):
        self.assertRaises(parse.ParseError, parser.parse, parse.State(text))

    def test_comma_list(self):
        p = rfc7230.comma_list(rfc7230.token) + parse.eof
        self.assertParse(p, '', [])
        self.assertParse(p, ' , ,, , ,', [])
        self.assertParse(p, 'foo', ['foo'])
        self.assertParse(p, 'foo,bar', ['foo', 'bar'])
        self.assertParse(p, 'foo, bar,', ['foo', 'bar'])
        self.assertParse(p, ', ,,,foo, ,bar, baz, ,, ,', ['foo', 'bar', 'baz'])
        self.assertNoParse(p, 'foo,"bar"')
        self.assertNoParse(p, 'foo;bar')

    def test_comma_list1(self):
        p = rfc7230.comma_list1(rfc7230.token) + parse.eof
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
        p = rfc7230.transfer_coding + parse.eof
        self.assertParse(p, 'chunked', Parametrized(tc.chunked, []))
        self.assertParse(p, 'foo',
                         Parametrized(TransferCoding(u'foo'), []))
        self.assertParse(p, 'foo ; bar = baz ; qux = "\\"xyzzy\\""',
                         Parametrized(TransferCoding(u'foo'),
                                      [(u'bar', u'baz'),
                                       (u'qux', u'"xyzzy"')]))
        self.assertNoParse(p, '')
        self.assertNoParse(p, 'foo;???')
        self.assertNoParse(p, 'foo;"bar"="baz"')

        p = rfc7230.t_codings + parse.eof
        self.assertParse(p, 'gzip;q=0.345', Parametrized(tc.gzip,
                                                         [(u'q', 0.345)]))
        self.assertParse(p, 'gzip; Q=1.0', Parametrized(tc.gzip, [(u'Q', 1)]))
        self.assertParse(p, 'trailers', u'trailers')
        self.assertNoParse(p, 'gzip;q=2.0')

    def test_media_type(self):
        p = rfc7231.media_type + parse.eof
        self.assertParse(
            p, 'Text/HTML; Charset="utf-8"',
            Parametrized(media.text_html, [(u'charset', u'utf-8')]))
        self.assertParse(
            p, 'application/vnd.github.v3+json',
            Parametrized(MediaType(u'application/vnd.github.v3+json'), []))

    def test_accept(self):
        p = rfc7231.accept + parse.eof
        self.assertParse(
            p,
            'text/html;charset="utf-8";Q=1;profile="mobile", '
            'text/plain;Q=0.2, text/*;Q=0.02, */*;Q=0.01',
            [
                Parametrized(
                    Parametrized(media.text_html, [(u'charset', u'utf-8')]),
                    [(u'q', 1), (u'profile', u'mobile')]
                ),
                Parametrized(
                    Parametrized(media.text_plain, []),
                    [(u'q', 0.2)]
                ),
                Parametrized(
                    Parametrized(MediaType(u'text/*'), []),
                    [(u'q', 0.02)]
                ),
                Parametrized(
                    Parametrized(MediaType(u'*/*'), []),
                    [(u'q', 0.01)]
                ),
            ]
        )
        self.assertParse(
            p, '*/*',
            [Parametrized(Parametrized(MediaType(u'*/*'), []), [])])
        self.assertParse(
            p, 'application/json',
            [Parametrized(Parametrized(media.application_json, []), [])])
        self.assertParse(
            p, 'audio/*; q=0.2, audio/basic',
            [
                Parametrized(Parametrized(MediaType(u'audio/*'), []),
                             [(u'q', 0.2)]),
                Parametrized(Parametrized(media.audio_basic, []), []),
            ])
        self.assertParse(
            p, 'text/plain; q=0.5, text/html, text/x-dvi; q=0.8, text/x-c',
            [
                Parametrized(Parametrized(media.text_plain, []),
                             [(u'q', 0.5)]),
                Parametrized(Parametrized(media.text_html, []), []),
                Parametrized(Parametrized(MediaType(u'text/x-dvi'), []),
                             [(u'q', 0.8)]),
                Parametrized(Parametrized(MediaType(u'text/x-c'), []), []),
            ])
        self.assertParse(
            p, ', ,text/*, text/plain,,, text/plain;format=flowed, */*',
            [
                Parametrized(Parametrized(MediaType(u'text/*'), []), []),
                Parametrized(Parametrized(media.text_plain, []), []),
                Parametrized(
                    Parametrized(media.text_plain, [(u'format', u'flowed')]),
                    []
                ),
                Parametrized(Parametrized(MediaType(u'*/*'), []), []),
            ])
        self.assertParse(p, '', [])
        self.assertParse(p, ',', [])
        self.assertNoParse(p, 'text/html;q=foo-bar')
        self.assertNoParse(p, 'text/html;q=0.12345')
        self.assertNoParse(p, 'text/html;q=1.23456')
        self.assertNoParse(p, 'text/html;foo=bar;q=1.23456')
        self.assertNoParse(p, 'text/html=0.123')
        self.assertNoParse(p, 'text/html,q=0.123')
        self.assertNoParse(p, 'text/html q=0.123')
        self.assertNoParse(p, 'text/html;text/plain')
        self.assertNoParse(p, 'text/html;;q=0.123')
        self.assertNoParse(p, 'text/html;q="0.123"')

    def test_accept_charset(self):
        p = rfc7231.accept_charset + parse.eof
        self.assertParse(
            p, 'iso-8859-5, unicode-1-1 ; q=0.8',
            [
                Parametrized(u'iso-8859-5', None),
                Parametrized(u'unicode-1-1', 0.8)
            ]
        )

    def test_accept_encoding(self):
        p = rfc7231.accept_encoding + parse.eof
        self.assertParse(
            p, 'compress, gzip',
            [Parametrized(cc.compress, None), Parametrized(cc.gzip, None)])
        self.assertParse(p, '', [])
        self.assertParse(p, '*', [Parametrized(ContentCoding(u'*'), None)])
        self.assertParse(
            p, 'compress;q=0.5, gzip;q=1.0',
            [Parametrized(cc.compress, 0.5), Parametrized(cc.gzip, 1)])
        self.assertParse(
            p, 'gzip;q=1.0, identity; q=0.5, *;q=0',
            [
                Parametrized(cc.gzip, 1),
                Parametrized(ContentCoding(u'identity'), 0.5),
                Parametrized(ContentCoding(u'*'), 0)
            ]
        )
        self.assertNoParse(p, 'gzip; identity')
        self.assertNoParse(p, 'gzip, q=1.0')

    def test_accept_language(self):
        p = rfc7231.accept_language + parse.eof
        self.assertParse(
            p, 'da, en-gb;q=0.8, en;q=0.7',
            [
                Parametrized(LanguageTag(u'da'), None),
                Parametrized(LanguageTag(u'en-GB'), 0.8),
                Parametrized(LanguageTag(u'en'), 0.7),
            ]
        )
        self.assertParse(
            p, 'en, *; q=0',
            [
                Parametrized(LanguageTag(u'en'), None),
                Parametrized(LanguageTag(u'*'), 0),
            ]
        )
        self.assertParse(p, 'da', [Parametrized(LanguageTag(u'da'), None)])
        self.assertNoParse(p, 'en_GB')
        self.assertNoParse(p, 'x1, x2')
        self.assertNoParse(p, 'en; q = 0.7')

    def test_request_target(self):
        p = rfc7230.origin_form + parse.eof
        self.assertParse(p, '/where?q=now')
        self.assertNoParse(p, '/hello world')

        p = rfc7230.absolute_form + parse.eof
        self.assertParse(p, 'http://www.example.com:80')

        p = rfc7230.authority_form + parse.eof
        self.assertParse(p, 'www.example.com:80')
        self.assertParse(p, '[::0]:8080')

        p = rfc7230.asterisk_form + parse.eof
        self.assertParse(p, '*')

        p = rfc3986.absolute_uri + parse.eof
        self.assertParse(p, 'ftp://ftp.is.co.za/rfc/rfc1808.txt')
        self.assertParse(p, 'http://www.ietf.org/rfc/rfc2396.txt')
        self.assertParse(p, 'ldap://[2001:db8::7]/c=GB?objectClass?one')
        self.assertParse(p, 'mailto:John.Doe@example.com')
        self.assertParse(p, 'news:comp.infosystems.www.servers.unix')
        self.assertParse(p, 'tel:+1-816-555-1212')
        self.assertParse(p, 'telnet://192.0.2.16:80/')
        self.assertParse(p,
                         'urn:oasis:names:specification:docbook:dtd:xml:4.1.2')

    def test_partial_uri(self):
        p = rfc7230.partial_uri + parse.eof
        self.assertParse(p, '/')
        self.assertParse(p, '/foo/bar?baz=qux&xyzzy=123')
        self.assertParse(p, 'foo/bar/')
        self.assertParse(p, '//example.net/static/ui.js')
        self.assertNoParse(p, '/foo#bar=baz')

    def test_via(self):
        p = rfc7230.via + parse.eof
        self.assertParse(p, '1.0 fred, 1.1 p.example.net',
                         [(Versioned(u'HTTP', u'1.0'), u'fred', None),
                          (Versioned(u'HTTP', u'1.1'),
                           u'p.example.net', None)])
        self.assertParse(
            p,
            r', FSTR/2 balancer4g-p1.example.com  '
            r'(Acme Web Accelerator 4.1 \(Debian\)), '
            r'1.1 proxy1,',
            [
                (
                    Versioned(u'FSTR', u'2'),
                    u'balancer4g-p1.example.com',
                    'Acme Web Accelerator 4.1 (Debian)'
                ),
                (
                    Versioned(u'HTTP', u'1.1'),
                    u'proxy1',
                    None
                )
            ]
        )
        self.assertNoParse(p, 'proxy1, proxy2')

    def test_protocol(self):
        p = rfc7230.protocol + parse.eof
        self.assertParse(p, 'h2c', (u'h2c', None))
        self.assertParse(p, 'FSTR/2', (u'FSTR', u'2'))
        self.assertNoParse(p, '/2')

    def test_user_agent(self):
        p = rfc7231.user_agent + parse.eof
        self.assertParse(
            p,
            'Mozilla/5.0 '
            '(compatible; Vanadium '
            r'\(a nice browser btw, check us out: '
            r'http://vanadium.example/?about_us\)) '
            'libVanadium/0.11a-pre9',
            [
                Versioned(ProductName(u'Mozilla'), u'5.0'),
                u'compatible; Vanadium '
                u'(a nice browser btw, check us out: '
                u'http://vanadium.example/?about_us)',
                Versioned(ProductName(u'libVanadium'), u'0.11a-pre9')
            ])
        self.assertParse(
            p,
            'Mozilla/5.0 (X11; Linux x86_64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/37.0.2062.120 Safari/537.36',
            [
                Versioned(ProductName(u'Mozilla'), u'5.0'),
                u'X11; Linux x86_64',
                Versioned(ProductName(u'AppleWebKit'), u'537.36'),
                u'KHTML, like Gecko',
                Versioned(ProductName(u'Chrome'), u'37.0.2062.120'),
                Versioned(ProductName(u'Safari'), u'537.36')
            ])

    def test_http_date(self):
        p = rfc7231.http_date + parse.eof
        self.assertParse(p, 'Sun, 06 Nov 1994 08:49:37 GMT',
                         datetime(1994, 11, 6, 8, 49, 37))
        self.assertParse(p, 'Sunday, 06-Nov-94 08:49:37 GMT',
                         datetime(1994, 11, 6, 8, 49, 37))
        self.assertParse(p, 'Sun Nov  6 08:49:37 1994',
                         datetime(1994, 11, 6, 8, 49, 37))
        self.assertParse(p, 'Sun Nov 16 08:49:37 1994',
                         datetime(1994, 11, 16, 8, 49, 37))
        self.assertNoParse(p, 'Sun, 29 Feb 2015 14:11:06 GMT')
        self.assertNoParse(p, 'Wed, 13 Jan 2016 24:09:06 GMT')

    def test_acceptable_ranges(self):
        p = rfc7233.acceptable_ranges + parse.eof
        self.assertParse(p, 'none', [])
        self.assertParse(p, 'NONE', [])
        self.assertParse(p, 'none,', [RangeUnit(u'none')])
        self.assertParse(p, ', ,Bytes, Pages',
                         [unit.bytes, RangeUnit(u'pages')])

    def test_range(self):
        p = rfc7233.range + parse.eof
        self.assertParse(
            p, 'bytes=0-499',
            RangeSpecifier(unit.bytes, [(0, 499)]))
        self.assertParse(
            p, 'bytes=500-999',
            RangeSpecifier(unit.bytes, [(500, 999)]))
        self.assertParse(
            p, 'bytes=9500-',
            RangeSpecifier(unit.bytes, [(9500, None)]))
        self.assertParse(
            p, 'bytes=-500',
            RangeSpecifier(unit.bytes, [(None, 500)]))
        self.assertParse(
            p, 'BYTES=0-0, -1',
            RangeSpecifier(unit.bytes, [(0, 0), (None, 1)]))
        self.assertParse(
            p, 'Bytes=,500-700 ,601-999, ,',
            RangeSpecifier(unit.bytes, [(500, 700), (601, 999)]))
        self.assertParse(
            p, 'pages=1-5',
            RangeSpecifier(RangeUnit(u'pages'), u'1-5'))

        self.assertNoParse(p, 'bytes=1+2-3')
        self.assertNoParse(p, 'pages=1-5, 6-7')
        self.assertNoParse(p, '1-5')

    def test_content_range(self):
        p = rfc7233.content_range + parse.eof
        self.assertParse(
            p, 'bytes 42-1233/1234',
            ContentRange(unit.bytes, ((42, 1233), 1234)))
        self.assertParse(
            p, 'bytes 42-1233/*',
            ContentRange(unit.bytes, ((42, 1233), None)))
        self.assertParse(
            p, 'bytes */1234',
            ContentRange(unit.bytes, (None, 1234)))
        self.assertParse(
            p, 'pages 1, 3, 5-7',
            ContentRange(RangeUnit(u'pages'), '1, 3, 5-7'))
        self.assertNoParse(p, 'bytes 42-1233')
        self.assertNoParse(p, 'bytes *')
        self.assertNoParse(p, 'bytes */*')
        self.assertNoParse(p, 'bytes 42/1233')
        self.assertNoParse(p, 'bytes 42, 43, 44')


class TestRequest(unittest.TestCase):

    @staticmethod
    def parse(inbound, scheme='http'):
        outbound = ('HTTP/1.1 400 Bad Request\r\n'
                    'Date: Thu, 28 Jan 2016 19:30:21 GMT\r\n'
                    'Content-Length: 0\r\n'
                    '\r\n') * 10        # Enough to cover all requests
        conn = analyze_streams(inbound, outbound, scheme=scheme)
        TextReport.render([conn], StringIO())
        HTMLReport.render([conn], StringIO())
        return [exch.request for exch in conn.exchanges]

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
        [req1, req2, req3] = self.parse(stream)

        self.assertEquals(req1.method, u'GET')
        self.assertEquals(repr(req1.method), "Method(u'GET')")
        self.assertEquals(req1.target, u'/foo/bar/baz?qux=xyzzy')
        self.assertEquals(req1.version, http11)
        self.assertEquals(req1.header_entries[0].name, u'Host')
        self.assertEquals(req1.header_entries[0].value, 'example.com')
        self.assertEquals(req1.header_entries[1].name, u'X-Foo')
        self.assertEquals(req1.header_entries[1].value, 'bar, baz')
        self.assertEquals(repr(req1.header_entries[1]), '<HeaderEntry X-Foo>')
        self.assertEquals(repr(req1), '<RequestView GET>')
        self.assertEquals(repr(req1.inner), '<Request GET>')

        self.assertEquals(req2.method, u'POST')
        self.assertEquals(req2.target, u'/foo/bar/')
        self.assertEquals(req2.header_entries[1].name, u'content-length')
        self.assertEquals(req2.headers.content_length.value, 21)
        self.assertEquals(req2.headers.content_length.is_present, True)
        self.assertEquals(repr(req2.headers.content_length),
                          '<SingleHeaderView Content-Length>')
        self.assertEquals(req2.body, 'Привет мир!\n')

        self.assertEquals(req3.method, u'OPTIONS')
        self.assertEquals(req3.target, u'*')

    def test_unparseable_framing(self):
        self.assertEquals(self.parse('GET ...'), [])

    def test_unparseable_body(self):
        stream = ('POST / HTTP/1.1\r\n'
                  'Host: example.com\r\n'
                  'Content-Length: 90\r\n'
                  '\r\n'
                  'wololo')
        [req1] = self.parse(stream)
        self.assertEqual(req1.method, u'POST')
        self.assertEqual(req1.headers.content_length.value, 90)
        self.assert_(req1.body is Unparseable)

    def test_unparseable_content_length(self):
        stream = ('POST / HTTP/1.1\r\n'
                  'Host: example.com\r\n'
                  'Content-Length: 4 5 6\r\n'
                  '\r\n'
                  'quux')
        [req1] = self.parse(stream)
        self.assert_(req1.body is Unparseable)

    def test_unparseable_following_parseable(self):
        stream = ('GET / HTTP/1.1\r\n'
                  'Host: example.com\r\n'
                  '\r\n'
                  'GET /\r\n'
                  'Host: example.com\r\n')
        [req1] = self.parse(stream)
        self.assertEqual(req1.method, u'GET')
        self.assert_(req1.body is None)

    def test_transfer_codings(self):
        stream = ('POST / HTTP/1.1\r\n'
                  'Host: example.com\r\n'
                  'Transfer-Encoding: foo\r\n'
                  'Transfer-Encoding:   ,\r\n'
                  'Transfer-Encoding: gzip, chunked\r\n'
                  '\r\n'
                  '0\r\n'
                  '\r\n')
        [req] = self.parse(stream)
        self.assert_(req.body is Unparseable)
        self.assertEqual(list(req.headers.transfer_encoding),
                         [Parametrized(u'foo', []),
                          Unparseable,
                          Parametrized(u'gzip', []),
                          Parametrized(u'chunked', [])])
        self.assertEqual(req.annotations[(False, 1)],
                         [TransferCoding(u'foo')])
        self.assert_((False, 2) not in req.annotations)
        self.assertEqual(req.annotations[(False, 3)],
                         [TransferCoding(u'gzip'), ', ',
                          TransferCoding(u'chunked')])

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
        [req1] = self.parse(stream)
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
        [req] = self.parse(stream)
        self.assertEqual(req.body, '')

    def test_parse_chunked_no_chunks(self):
        stream = ('POST / HTTP/1.1\r\n'
                  'Host: example.com\r\n'
                  'Transfer-encoding:  chunked\r\n'
                  '\r\n'
                  'GET / HTTP/1.1\r\n'
                  'Host: example.com\r\n'
                  '\r\n')
        [req] = self.parse(stream)
        self.assert_(req.body is Unparseable)

    def test_effective_uri_1(self):
        stream = ('GET /pub/WWW/TheProject.html HTTP/1.1\r\n'
                  'Host: www.example.org:8080\r\n'
                  '\r\n')
        [req] = self.parse(stream)
        self.assertEqual(
            req.effective_uri,
            'http://www.example.org:8080/pub/WWW/TheProject.html')

    def test_effective_uri_2(self):
        stream = ('GET /pub/WWW/TheProject.html HTTP/1.0\r\n'
                  '\r\n')
        [req] = self.parse(stream)
        self.assert_(req.effective_uri is None)

    def test_effective_uri_3(self):
        stream = ('OPTIONS * HTTP/1.1\r\n'
                  'Host: www.example.org\r\n'
                  '\r\n')
        [req] = self.parse(stream, scheme='https')
        self.assertEqual(req.effective_uri, 'https://www.example.org')

    def test_effective_uri_4(self):
        stream = ('GET myproto://www.example.org/index.html HTTP/1.1\r\n'
                  'Host: www.example.org\r\n'
                  '\r\n')
        [req] = self.parse(stream)
        self.assertEqual(req.effective_uri,
                         'myproto://www.example.org/index.html')

    def test_cache_control(self):
        stream = ('GET / HTTP/1.1\r\n'
                  'Host: example.com\r\n'
                  'Cache-Control: max-age="3600", max-stale=60,\r\n'
                  'Cache-Control: "foo bar"\r\n'
                  'Via: 1.1 baz\r\n'
                  'Cache-Control: qux="xyzzy 123", ,no-transform, abcde\r\n'
                  'Cache-Control: min-fresh, no-store=yes\r\n'
                  'Pragma: no-cache, foo, bar=baz, qux="xyzzy"\r\n'
                  'Pragma: no-cache=krekfewhrfk\r\n'
                  '\r\n')
        [req] = self.parse(stream)
        self.assertEqual(req.headers.cache_control.value,
                         [Parametrized(cache.max_age, 3600),
                          Parametrized(cache.max_stale, 60),
                          Unparseable,
                          Parametrized(CacheDirective(u'qux'), 'xyzzy 123'),
                          Parametrized(cache.no_transform, None),
                          Parametrized(CacheDirective(u'abcde'), None),
                          Parametrized(cache.min_fresh, Unparseable),
                          Parametrized(cache.no_store, None)])
        self.assertEqual(req.headers.pragma.value,
                         [u'no-cache',
                          (u'foo', None),
                          (u'bar', u'baz'),
                          (u'qux', 'xyzzy'),
                          Unparseable])

        self.assert_(cache.max_age in req.headers.cache_control)
        self.assertEqual(req.headers.cache_control.max_age, 3600)

        self.assert_(cache.max_stale in req.headers.cache_control)
        self.assertEqual(req.headers.cache_control.max_stale, 60)

        self.assertEqual(
            req.headers.cache_control[CacheDirective(u'qux')],
            'xyzzy 123')

        self.assert_(cache.no_transform in req.headers.cache_control)
        self.assertEqual(req.headers.cache_control.no_transform, True)

        self.assertEqual(
            req.headers.cache_control[CacheDirective(u'abcde')],
            True)

        self.assert_(req.headers.cache_control.no_cache is None)

        self.assert_(cache.min_fresh in req.headers.cache_control)
        self.assert_(req.headers.cache_control.min_fresh is Unparseable)

        self.assert_(cache.no_store in req.headers.cache_control)
        self.assertEqual(req.headers.cache_control.no_store, True)

        self.assert_(cache.only_if_cached not in req.headers.cache_control)


class TestResponse(unittest.TestCase):

    @staticmethod
    def req(method_):
        return str(
            '%s / HTTP/1.1\r\n'
            'Host: example.com\r\n'
            'Content-Length: 0\r\n'
            '\r\n' % method_
        )

    @staticmethod
    def parse(inbound, outbound, scheme='http'):
        conn = analyze_streams(inbound, outbound, scheme)
        TextReport.render([conn], StringIO())
        HTMLReport.render([conn], StringIO())
        return [exch.responses for exch in conn.exchanges]

    def test_analyze_exchange(self):
        req = Request('http',
                      'GET', '/', 'HTTP/1.1',
                      [('Host', 'example.com')])
        self.assertEqual(repr(req), '<Request GET>')
        resp1 = Response(req,
                         'HTTP/1.1', 123, 'Please wait', [])
        self.assertEqual(repr(resp1), '<Response 123>')
        resp2 = Response(req,
                         'HTTP/1.1', 200, 'OK',
                         [('Content-Length', 14)],
                         'Hello world!\r\n')
        exch = analyze_exchange(req, [resp1, resp2])
        self.assertEquals(repr(exch),
                          'Exchange(<RequestView GET>, '
                          '[<ResponseView 123>, <ResponseView 200>])')
        self.assert_(isinstance(exch.request.method, Method))
        self.assert_(isinstance(exch.request.version, HTTPVersion))
        self.assert_(isinstance(exch.request.header_entries[0].name,
                                FieldName))
        self.assert_(isinstance(exch.responses[0].version, HTTPVersion))
        self.assert_(isinstance(exch.responses[0].status, StatusCode))
        self.assert_(isinstance(exch.responses[1].header_entries[0].name,
                                FieldName))

    def test_parse_responses(self):
        inbound = self.req(m.HEAD) + self.req(m.POST) + self.req(m.POST)
        stream = ('HTTP/1.1 200 OK\r\n'
                  'Content-Length: 16\r\n'
                  '\r\n'
                  'HTTP/1.1 100 Continue\r\n'
                  '\r\n'
                  "HTTP/1.1 100 Keep On Rollin' Baby\r\n"
                  '\r\n'
                  'HTTP/1.1 200 OK\r\n'
                  'Content-Length: 16\r\n'
                  '\r\n'
                  'Hello world!\r\n'
                  '\r\n'
                  'HTTP/1.1 101 Switching Protocols\r\n'
                  'Upgrade: wololo\r\n'
                  '\r\n')
        [[resp1_1], [resp2_1, resp2_2, resp2_3], [resp3_1]] = \
            self.parse(inbound, stream)

        self.assertEquals(resp1_1.status, 200)
        self.assertEquals(repr(resp1_1.status), 'StatusCode(200)')
        self.assertEquals(resp1_1.headers.content_length.value, 16)
        self.assert_(resp1_1.body is None)

        self.assertEquals(resp2_1.status, 100)
        self.assertEquals(resp2_1.reason, 'Continue')
        self.assertEquals(resp2_2.status, 100)
        self.assertEquals(resp2_2.reason, "Keep On Rollin' Baby")
        self.assertEquals(resp2_3.status, 200)
        self.assertEquals(resp2_3.headers.content_length.value, 16)
        self.assertEquals(resp2_3.body, 'Hello world!\r\n\r\n')

        self.assertEquals(resp3_1.status, 101)
        self.assertEquals(resp3_1.header_entries[0].value, 'wololo')
        self.assert_(resp3_1.body is None)

    def test_parse_responses_not_enough_requests(self):
        inbound = self.req(m.POST)
        stream = ('HTTP/1.1 200 OK\r\n'
                  'Content-Length: 16\r\n'
                  '\r\n'
                  'Hello world!\r\n'
                  '\r\n'
                  'HTTP/1.1 101 Switching Protocols\r\n'
                  '\r\n')
        [[resp]] = self.parse(inbound, stream)
        self.assertEquals(resp.body, 'Hello world!\r\n\r\n')

    def test_parse_responses_bad_framing(self):
        self.assertEquals(self.parse(self.req(m.POST), 'HTTP/1.1 ...'), [])

    def test_parse_responses_implicit_framing(self):
        inbound = self.req(m.POST)
        stream = ('HTTP/1.1 200 OK\r\n'
                  '\r\n'
                  'Hello world!\r\n')
        [[resp1]] = self.parse(inbound, stream)
        self.assertEqual(resp1.body, 'Hello world!\r\n')

    def test_warning(self):
        inbound = self.req(m.GET)
        stream = ('HTTP/1.1 200 0K\r\n'
                  'Content-Type: text/plain\r\n'
                  'Warning: 123 - "something"\r\n'
                  'Warning: 234 [::0]:8080 "something else"\r\n'
                  '    "Thu, 28 Jan 2016 08:22:04 GMT" \r\n'
                  'Warning: 345 - forgot to quote this one\r\n'
                  'Warning: 456 baz "qux", 567 - "xyzzy"\r\n'
                  '\r\n'
                  'Hello world!\r\n')
        [[resp1]] = self.parse(inbound, stream)
        self.assertEqual(
            resp1.headers.warning.value,
            [WarningValue(WarnCode(123), u'-', 'something', None),
             WarningValue(WarnCode(234), u'[::0]:8080', 'something else',
                          datetime(2016, 1, 28, 8, 22, 4)),
             Unparseable,
             WarningValue(WarnCode(456), u'baz', 'qux', None),
             WarningValue(WarnCode(567), u'-', 'xyzzy', None)])
        self.assertEqual(repr(resp1.headers.warning.value[0].code),
                         'WarnCode(123)')
        self.assert_(WarnCode(123) in resp1.headers.warning)
        self.assert_(WarnCode(567) in resp1.headers.warning)
        self.assert_(WarnCode(199) not in resp1.headers.warning)


class TestFromFiles(unittest.TestCase):

    @classmethod
    def load_tests(cls):
        data_path = os.path.abspath(os.path.join(__file__, '..', 'test_data'))
        if os.path.isdir(data_path):
            for name in os.listdir(data_path):
                cls.make_test(data_path, name)
        cls.covered = set()
        cls.examples_filename = os.environ.get('WRITE_EXAMPLES_TO')
        cls.examples = {} if cls.examples_filename else None

    @classmethod
    def make_test(cls, data_path, name):
        filename = os.path.join(data_path, name)
        test_name = name.split('.')[0]
        def test(self):
            self.run_test(filename)
        setattr(cls, 'test_%s' % test_name, test)

    def run_test(self, filename, scheme=None):
        if '.' in filename:
            _, scheme = filename.split('.')
        else:
            scheme = 'http'
        if scheme == 'noscheme':
            scheme = None

        with open(filename) as f:
            data = f.read()
        header, data = data.split('======== BEGIN INBOUND STREAM ========\r\n')
        inb, outb = data.split('======== BEGIN OUTBOUND STREAM ========\r\n')
        lines = [ln for ln in header.splitlines() if not ln.startswith('#')]
        line = lines[0]
        expected = sorted(int(n) for n in line.split())

        conn = analyze_streams(inb, outb, scheme=scheme)
        buf = StringIO()
        TextReport.render([conn], buf)
        actual = sorted(int(ln[5:9]) for ln in buf.getvalue().splitlines()
                        if ln.startswith('**** '))
        self.covered.update(actual)
        self.assertEquals(expected, actual)

        HTMLReport.render([conn], StringIO())

        if self.examples is not None:
            for ident, ctx in conn.collect_complaints():
                self.examples.setdefault(ident, ctx)

    def test_all_notices_covered(self):
        self.assertEquals(self.covered, set(notices))
        if self.examples is not None:
            self.assertEquals(self.covered, set(self.examples))
            with open(self.examples_filename, 'w') as f:
                f.write(render_notice_examples(
                    (notices[ident], ctx)
                    for ident, ctx in sorted(self.examples.items())
                ))

TestFromFiles.load_tests()


if __name__ == '__main__':
    unittest.main()
