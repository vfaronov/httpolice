# -*- coding: utf-8; -*-

from six.moves import StringIO
from datetime import datetime
import io
import os
import pickle
import random
import string
import unittest

import six

from httpolice import (
    Exchange,
    analyze_exchange,
    analyze_streams,
)
from httpolice import parse
from httpolice.known import cache, cc, h, header, hsts, m, media, st, tc, unit
from httpolice.notice import notices
from httpolice.reports import html_report, text_report
from httpolice.reports.html import render_notice_examples
from httpolice.structure import (
    AuthScheme,
    CacheDirective,
    CaseInsensitive,
    ContentCoding,
    ContentRange,
    FieldName,
    HeaderEntry,
    HSTSDirective,
    HTTPVersion,
    LanguageTag,
    Method,
    MediaType,
    Parametrized,
    ProductName,
    RangeSpecifier,
    RangeUnit,
    RelationType,
    Request,
    Response,
    StatusCode,
    TransferCoding,
    Unavailable,
    Versioned,
    WarnCode,
    WarningValue,
    http10,
    http11,
)
from httpolice.syntax import rfc3986, rfc5988, rfc7230, rfc7231, rfc7233


def load_test_file(filename):
    if '.' in filename:
        scheme = filename.split('.')[-1]
    else:
        scheme = u'http'
    if scheme == u'noscheme':
        scheme = None

    with io.open(filename, 'rb') as f:
        data = f.read()
    header, data = data.split(b'======== BEGIN INBOUND STREAM ========\r\n')
    inb, outb = data.split(b'======== BEGIN OUTBOUND STREAM ========\r\n')
    header = header.decode('utf-8')
    lines = [ln for ln in header.splitlines() if not ln.startswith('#')]
    line = lines[0]
    expected = sorted(int(n) for n in line.split())

    return inb, outb, scheme, expected


def random_token():
    return ''.join(random.choice(string.ascii_letters + string.digits)
                   for _ in range(random.randint(1, 10))).encode('iso-8859-1')

def binary_garbage():
    return b''.join(six.int2byte(random.randint(0, 255))
                    for _ in range(10, 100))

fuzzers = [random_token, binary_garbage,
           lambda: b',', lambda: b'"', lambda: b'']

def make_header_value():
    return b' '.join(random.choice(fuzzers)()
                     for _ in range(random.randint(0, 10)))



class TestCommon(unittest.TestCase):

    def test_data_structures(self):
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


class TestSyntax(unittest.TestCase):

    def assertParse(self, parser, text, result=None):
        r = parse.Stream(text).parse(parser, to_eof=True)
        if result is Unavailable:
            self.assertIs(r, Unavailable)
        elif result is not None:
            self.assertEqual(r, result)

    def assertNoParse(self, parser, text):
        self.assertRaises(parse.ParseError, parse.Stream(text).parse,
                          parser, to_eof=True)

    def test_parser_edge_cases(self):
        # Our parser implementation is general enough that
        # some of its branches are not being exercised by our regular tests,
        # so I had to come up with these contrived examples to test them.

        p = parse.many(rfc7230.tchar)                      > parse.named(u'p')
        p1 = '1' * p                                       > parse.named(u'p1')
        p2 = '11' * p * parse.skip('\n')                   > parse.named(u'p2')
        self.assertParse(p1 | p2, b'11abc', (u'1', [u'1', u'a', u'b', u'c']))
        self.assertParse(p1 | p2, b'11abc\n', (u'11', [u'a', u'b', u'c']))

        p = parse.recursive()                              > parse.named(u'p')
        p.rec = (rfc7230.tchar * p |
                 parse.subst(None) << parse.empty)
        self.assertParse(p, b'abc', (u'a', (u'b', (u'c', None))))

        p = parse.literal('ab')                            > parse.named(u'p')
        p0 = parse.subst(u'') << parse.empty | p           > parse.named(u'p0')
        p1 = 'xab' * p0                                    > parse.named(u'p1')
        p2 = 'x' * parse.string(p0) * '!'                  > parse.named(u'p2')
        self.assertParse(p1 | p2, b'xabab', (u'xab', u'ab'))
        self.assertParse(p1 | p2, b'xabab!', (u'x', u'abab', u'!'))

        p = parse.empty | parse.literal('a')               > parse.named(u'p')
        p0 = p * 'x'                                       > parse.named(u'x')
        self.assertParse(p0, b'x', u'x')

    def test_comma_list(self):
        p = rfc7230.comma_list(rfc7230.token)
        self.assertParse(p, b'', [])
        self.assertParse(p, b', ,, , ,', [])
        self.assertParse(p, b'foo', [u'foo'])
        self.assertParse(p, b'foo,bar', [u'foo', u'bar'])
        self.assertParse(p, b'foo, bar,', [u'foo', u'bar'])
        self.assertParse(p, b', ,,,foo, ,bar, baz, ,, ,',
                         [u'foo', u'bar', u'baz'])
        self.assertNoParse(p, b'foo,"bar"')
        self.assertNoParse(p, b'foo;bar')

    def test_comma_list1(self):
        p = rfc7230.comma_list1(rfc7230.token)
        self.assertNoParse(p, b'')
        self.assertNoParse(p, b'  \t ')
        self.assertNoParse(p, b' , ,, , ,')
        self.assertParse(p, b'foo', [u'foo'])
        self.assertParse(p, b'foo,bar', [u'foo', u'bar'])
        self.assertParse(p, b'foo, bar,', [u'foo', u'bar'])
        self.assertParse(p, b', ,,,foo, ,bar, baz, ,, ,',
                         [u'foo', u'bar', u'baz'])
        self.assertNoParse(p, b'foo,"bar"')
        self.assertNoParse(p, b'foo;bar')

    def test_comment(self):
        p = rfc7230.comment(include_parens=False)
        self.assertParse(p, b'(foo (bar \\) baz "( qux)") xyzzy \\123 )',
                         u'foo (bar ) baz "( qux)") xyzzy 123 ')
        self.assertParse(p,
                         u'(að láta (gera við) börn sín)'.encode('iso-8859-1'),
                         u'að láta (gera við) börn sín')
        self.assertNoParse(p, b'(foo "bar)" baz)')

    def test_transfer_coding(self):
        p = rfc7230.transfer_coding()
        self.assertParse(p, b'chunked', Parametrized(tc.chunked, []))
        self.assertParse(p, b'foo',
                         Parametrized(TransferCoding(u'foo'), []))
        self.assertParse(p, b'foo ; bar = baz ; qux = "\\"xyzzy\\""',
                         Parametrized(TransferCoding(u'foo'),
                                      [(u'bar', u'baz'),
                                       (u'qux', u'"xyzzy"')]))
        self.assertNoParse(p, b'')
        self.assertNoParse(p, b'foo;???')
        self.assertNoParse(p, b'foo;"bar"="baz"')

        p = rfc7230.t_codings
        self.assertParse(p, b'gzip;q=0.345',
                         Parametrized(Parametrized(tc.gzip, []), 0.345))
        self.assertParse(p, b'gzip; Q=1.0',
                         Parametrized(Parametrized(tc.gzip, []), 1))
        self.assertParse(p, b'trailers', u'trailers')
        self.assertNoParse(p, b'gzip;q=2.0')

    def test_media_type(self):
        p = rfc7231.media_type
        self.assertParse(
            p, b'Text/HTML; Charset="utf-8"',
            Parametrized(media.text_html, [(u'charset', u'utf-8')]))
        self.assertParse(
            p, b'application/vnd.github.v3+json',
            Parametrized(MediaType(u'application/vnd.github.v3+json'), []))

    def test_accept(self):
        p = rfc7231.Accept
        self.assertParse(
            p,
            b'text/html;charset="utf-8";Q=1;profile="mobile", '
            b'text/plain;Q=0.2, text/*;Q=0.02, */*;Q=0.01',
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
            p, b'*/*',
            [Parametrized(Parametrized(MediaType(u'*/*'), []), [])])
        self.assertParse(
            p, b'application/json',
            [Parametrized(Parametrized(media.application_json, []), [])])
        self.assertParse(
            p, b'audio/*; q=0.2, audio/basic',
            [
                Parametrized(Parametrized(MediaType(u'audio/*'), []),
                             [(u'q', 0.2)]),
                Parametrized(Parametrized(media.audio_basic, []), []),
            ])
        self.assertParse(
            p, b'text/plain; q=0.5, text/html, text/x-dvi; q=0.8, text/x-c',
            [
                Parametrized(Parametrized(media.text_plain, []),
                             [(u'q', 0.5)]),
                Parametrized(Parametrized(media.text_html, []), []),
                Parametrized(Parametrized(MediaType(u'text/x-dvi'), []),
                             [(u'q', 0.8)]),
                Parametrized(Parametrized(MediaType(u'text/x-c'), []), []),
            ])
        self.assertParse(
            p, b', ,text/*, text/plain,,, text/plain;format=flowed, */*',
            [
                Parametrized(Parametrized(MediaType(u'text/*'), []), []),
                Parametrized(Parametrized(media.text_plain, []), []),
                Parametrized(
                    Parametrized(media.text_plain, [(u'format', u'flowed')]),
                    []
                ),
                Parametrized(Parametrized(MediaType(u'*/*'), []), []),
            ])
        self.assertParse(p, b'', [])
        self.assertParse(p, b',', [])
        self.assertNoParse(p, b'text/html;q=foo-bar')
        self.assertNoParse(p, b'text/html;q=0.12345')
        self.assertNoParse(p, b'text/html;q=1.23456')
        self.assertNoParse(p, b'text/html;foo=bar;q=1.23456')
        self.assertNoParse(p, b'text/html=0.123')
        self.assertNoParse(p, b'text/html,q=0.123')
        self.assertNoParse(p, b'text/html q=0.123')
        self.assertNoParse(p, b'text/html;text/plain')
        self.assertNoParse(p, b'text/html;;q=0.123')
        self.assertNoParse(p, b'text/html;q="0.123"')

    def test_accept_charset(self):
        p = rfc7231.Accept_Charset
        self.assertParse(
            p, b'iso-8859-5, unicode-1-1 ; q=0.8',
            [
                Parametrized(u'iso-8859-5', None),
                Parametrized(u'unicode-1-1', 0.8)
            ]
        )

    def test_accept_encoding(self):
        p = rfc7231.Accept_Encoding
        self.assertParse(
            p, b'compress, gzip',
            [Parametrized(cc.compress, None), Parametrized(cc.gzip, None)])
        self.assertParse(p, b'', [])
        self.assertParse(p, b'*', [Parametrized(ContentCoding(u'*'), None)])
        self.assertParse(
            p, b'compress;q=0.5, gzip;q=1.0',
            [Parametrized(cc.compress, 0.5), Parametrized(cc.gzip, 1)])
        self.assertParse(
            p, b'gzip;q=1.0, identity; q=0.5, *;q=0',
            [
                Parametrized(cc.gzip, 1),
                Parametrized(ContentCoding(u'identity'), 0.5),
                Parametrized(ContentCoding(u'*'), 0)
            ]
        )
        self.assertNoParse(p, b'gzip; identity')
        self.assertNoParse(p, b'gzip, q=1.0')

    def test_accept_language(self):
        p = rfc7231.Accept_Language
        self.assertParse(
            p, b'da, en-gb;q=0.8, en;q=0.7',
            [
                Parametrized(LanguageTag(u'da'), None),
                Parametrized(LanguageTag(u'en-GB'), 0.8),
                Parametrized(LanguageTag(u'en'), 0.7),
            ]
        )
        self.assertParse(
            p, b'en, *; q=0',
            [
                Parametrized(LanguageTag(u'en'), None),
                Parametrized(LanguageTag(u'*'), 0),
            ]
        )
        self.assertParse(p, b'da', [Parametrized(LanguageTag(u'da'), None)])
        self.assertNoParse(p, b'en_GB')
        self.assertNoParse(p, b'x1, x2')
        self.assertNoParse(p, b'en; q = 0.7')

    def test_request_target(self):
        p = rfc7230.origin_form
        self.assertParse(p, b'/where?q=now')
        self.assertNoParse(p, b'/hello world')

        p = rfc7230.absolute_form
        self.assertParse(p, b'http://www.example.com:80')

        p = rfc7230.authority_form
        self.assertParse(p, b'www.example.com:80')
        self.assertParse(p, b'[::0]:8080')

        p = rfc7230.asterisk_form
        self.assertParse(p, b'*')

        p = rfc3986.absolute_URI
        self.assertParse(p, b'ftp://ftp.is.co.za/rfc/rfc1808.txt')
        self.assertParse(p, b'http://www.ietf.org/rfc/rfc2396.txt')
        self.assertParse(p, b'ldap://[2001:db8::7]/c=GB?objectClass?one')
        self.assertParse(p, b'mailto:John.Doe@example.com')
        self.assertParse(p, b'news:comp.infosystems.www.servers.unix')
        self.assertParse(p, b'tel:+1-816-555-1212')
        self.assertParse(p, b'telnet://192.0.2.16:80/')
        self.assertParse(
            p, b'urn:oasis:names:specification:docbook:dtd:xml:4.1.2')
        self.assertParse(p, b'http://[fe80::a%25en1]')      # RFC 6874

    def test_partial_uri(self):
        p = rfc7230.partial_URI
        self.assertParse(p, b'/')
        self.assertParse(p, b'/foo/bar?baz=qux&xyzzy=123')
        self.assertParse(p, b'foo/bar/')
        self.assertParse(p, b'//example.net/static/ui.js')
        self.assertNoParse(p, b'/foo#bar=baz')

    def test_via(self):
        p = rfc7230.Via
        self.assertParse(p, b'1.0 fred, 1.1 p.example.net',
                         [(Versioned(u'HTTP', u'1.0'), u'fred', None),
                          (Versioned(u'HTTP', u'1.1'),
                           u'p.example.net', None)])
        self.assertParse(
            p,
            br', FSTR/2 balancer4g-p1.example.com  '
            br'(Acme Web Accelerator 4.1 \(Debian\)), '
            br'1.1 proxy1,',
            [
                (
                    Versioned(u'FSTR', u'2'),
                    u'balancer4g-p1.example.com',
                    u'Acme Web Accelerator 4.1 (Debian)'
                ),
                (
                    Versioned(u'HTTP', u'1.1'),
                    u'proxy1',
                    None
                )
            ]
        )
        self.assertNoParse(p, b'proxy1, proxy2')

    def test_protocol(self):
        p = rfc7230.protocol
        self.assertParse(p, b'h2c', (u'h2c', None))
        self.assertParse(p, b'FSTR/2', (u'FSTR', u'2'))
        self.assertNoParse(p, b'/2')

    def test_user_agent(self):
        p = rfc7231.User_Agent
        self.assertParse(
            p,
            b'Mozilla/5.0 '
            b'(compatible; Vanadium '
            br'\(a nice browser btw, check us out: '
            br'http://vanadium.example/?about_us\)) '
            b'libVanadium/0.11a-pre9',
            [
                Versioned(ProductName(u'Mozilla'), u'5.0'),
                u'compatible; Vanadium '
                u'(a nice browser btw, check us out: '
                u'http://vanadium.example/?about_us)',
                Versioned(ProductName(u'libVanadium'), u'0.11a-pre9')
            ])
        self.assertParse(
            p,
            b'Mozilla/5.0 (X11; Linux x86_64) '
            b'AppleWebKit/537.36 (KHTML, like Gecko) '
            b'Chrome/37.0.2062.120 Safari/537.36',
            [
                Versioned(ProductName(u'Mozilla'), u'5.0'),
                u'X11; Linux x86_64',
                Versioned(ProductName(u'AppleWebKit'), u'537.36'),
                u'KHTML, like Gecko',
                Versioned(ProductName(u'Chrome'), u'37.0.2062.120'),
                Versioned(ProductName(u'Safari'), u'537.36')
            ])

    def test_http_date(self):
        p = rfc7231.HTTP_date
        self.assertParse(p, b'Sun, 06 Nov 1994 08:49:37 GMT',
                         datetime(1994, 11, 6, 8, 49, 37))
        self.assertParse(p, b'Sunday, 06-Nov-94 08:49:37 GMT',
                         datetime(1994, 11, 6, 8, 49, 37))
        self.assertParse(p, b'Sun Nov  6 08:49:37 1994',
                         datetime(1994, 11, 6, 8, 49, 37))
        self.assertParse(p, b'Sun Nov 16 08:49:37 1994',
                         datetime(1994, 11, 16, 8, 49, 37))
        self.assertParse(p, b'Sun Nov 36 08:49:37 1994', Unavailable)
        self.assertParse(p, b'Sun Nov 16 28:49:37 1994', Unavailable)
        self.assertNoParse(p, b'Foo, 13 Jan 2016 24:09:06 GMT')

    def test_acceptable_ranges(self):
        p = rfc7233.acceptable_ranges
        self.assertParse(p, b'none', [])
        self.assertParse(p, b'NONE', [])
        self.assertParse(p, b'none,', [RangeUnit(u'none')])
        self.assertParse(p, b', ,Bytes, Pages',
                         [unit.bytes, RangeUnit(u'pages')])

    def test_range(self):
        p = rfc7233.Range
        self.assertParse(
            p, b'bytes=0-499',
            RangeSpecifier(unit.bytes, [(0, 499)]))
        self.assertParse(
            p, b'bytes=500-999',
            RangeSpecifier(unit.bytes, [(500, 999)]))
        self.assertParse(
            p, b'bytes=9500-',
            RangeSpecifier(unit.bytes, [(9500, None)]))
        self.assertParse(
            p, b'bytes=-500',
            RangeSpecifier(unit.bytes, [(None, 500)]))
        self.assertParse(
            p, b'BYTES=0-0, -1',
            RangeSpecifier(unit.bytes, [(0, 0), (None, 1)]))
        self.assertParse(
            p, b'Bytes=,500-700 ,601-999, ,',
            RangeSpecifier(unit.bytes, [(500, 700), (601, 999)]))
        self.assertParse(
            p, b'pages=1-5',
            RangeSpecifier(RangeUnit(u'pages'), u'1-5'))

        self.assertNoParse(p, b'bytes=1+2-3')
        self.assertNoParse(p, b'pages=1-5, 6-7')
        self.assertNoParse(p, b'1-5')

    def test_content_range(self):
        p = rfc7233.Content_Range
        self.assertParse(
            p, b'bytes 42-1233/1234',
            ContentRange(unit.bytes, ((42, 1233), 1234)))
        self.assertParse(
            p, b'bytes 42-1233/*',
            ContentRange(unit.bytes, ((42, 1233), None)))
        self.assertParse(
            p, b'bytes */1234',
            ContentRange(unit.bytes, (None, 1234)))
        self.assertParse(
            p, b'pages 1, 3, 5-7',
            ContentRange(RangeUnit(u'pages'), u'1, 3, 5-7'))
        self.assertNoParse(p, b'bytes 42-1233')
        self.assertNoParse(p, b'bytes *')
        self.assertNoParse(p, b'bytes */*')
        self.assertNoParse(p, b'bytes 42/1233')
        self.assertNoParse(p, b'bytes 42, 43, 44')

    def test_link(self):
        p = rfc5988.Link
        self.assertParse(
            p,
            b'<http://example.com/TheBook/chapter2>; rel="previous"; '
            b'title="previous chapter"',
            [
                Parametrized(
                    u'http://example.com/TheBook/chapter2',
                    [
                        (u'rel', [RelationType(u'previous')]),
                        (u'title', u'previous chapter'),
                    ]
                )
            ],
        )
        self.assertParse(
            p, b'</>; rel="http://example.net/foo"',
            [Parametrized(u'/', [(u'rel', [u'http://example.net/foo'])])]
        )
        self.assertParse(
            p,
            b'</TheBook/chapter2>; '
            b'rel="previous"; title*=UTF-8\'de\'letztes%20Kapitel, '
            b'</TheBook/chapter4>; '
            b'rel="next"; title*=UTF-8\'de\'n%c3%a4chstes%20Kapitel',
            [
                Parametrized(
                    u'/TheBook/chapter2',
                    [
                        (u'rel', [RelationType(u'previous')]),
                        (u'title*', (u'UTF-8', u'de', u'letztes%20Kapitel')),
                    ]
                ),
                Parametrized(
                    u'/TheBook/chapter4',
                    [
                        (u'rel', [RelationType(u'next')]),
                        (u'Title*', (u'UTF-8', u'de',
                                     u'n%c3%a4chstes%20Kapitel')),
                    ]
                ),
            ]
        )
        self.assertParse(
            p,
            b'<http://example.org/>; '
            b'rel="start http://example.net/relation/other"',
            [
                Parametrized(
                    u'http://example.org/',
                    [
                        (u'REL', [RelationType(u'START'),
                                  u'http://example.net/relation/other']),
                    ]
                ),
            ]
        )
        self.assertParse(
            p, b'</>; rel=foo; type=text/plain; rel=bar; type=text/html',
            [
                Parametrized(
                    u'/',
                    [
                        (u'rel', [RelationType(u'foo')]),
                        (u'type', MediaType(u'text/plain')),
                        (u'type', MediaType(u'text/html')),
                    ]
                ),
            ]
        )
        self.assertParse(
            p,
            b'</foo/bar?baz=qux#xyzzy>  ;  media = whatever man okay? ; '
            b'hreflang=en-US',
            [
                Parametrized(
                    u'/foo/bar?baz=qux#xyzzy',
                    [
                        (u'media', u' whatever man okay?'),
                        (u'hreflang', LanguageTag(u'en-US')),
                    ]
                ),
            ]
        )
        self.assertParse(
            p, b'<foo>, <bar>, <>',
            [
                Parametrized(u'foo', []),
                Parametrized(u'bar', []),
                Parametrized(u'', []),
            ]
        )
        self.assertParse(
            p, b"<urn:foo:bar:baz>; MyParam* = ISO-8859-1'en'whatever",
            [
                Parametrized(
                    u'urn:foo:bar:baz',
                    [
                        (u'myparam*', (u'ISO-8859-1', u'en', u'whatever')),
                    ]
                ),
            ]
        )
        self.assertParse(
            p, b'<#me>; coolest; man; ever!',
            [
                Parametrized(
                    u'#me',
                    [(u'coolest', None), (u'man', None), (u'ever!', None)]
                ),
            ]
        )
        self.assertNoParse(p, b'</>; anchor=/index.html')
        self.assertNoParse(p, u'<http://пример.рф/>; rel=next'.encode('utf-8'))
        self.assertNoParse(p, b'</index.html>; title=Hello')
        self.assertNoParse(p, b'</index.html>; type="text/html;charset=utf-8"')
        self.assertNoParse(p, b"</>; title * = UTF-8''Hello")
        self.assertNoParse(p, b'</index.html>;')
        self.assertNoParse(p, b'</index.html>; rel=next;')


class TestRequest(unittest.TestCase):

    @staticmethod
    def parse(inbound, scheme=u'http'):
        outbound = (b'HTTP/1.1 400 Bad Request\r\n'
                    b'Date: Thu, 28 Jan 2016 19:30:21 GMT\r\n'
                    b'Content-Length: 0\r\n'
                    b'\r\n') * 10        # Enough to cover all requests
        exchanges = list(analyze_streams(inbound, outbound, scheme=scheme))
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
        self.assertEqual(repr(req1.header_entries[1]), '<HeaderEntry X-Foo>')
        self.assertEqual(repr(req1), '<RequestView GET>')
        self.assertEqual(repr(req1.inner), '<Request GET>')

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
        self.assertIs(req1.body, None)

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


class TestResponse(unittest.TestCase):

    @staticmethod
    def req(method_):
        return (
            '%s / HTTP/1.1\r\n'
            'Host: example.com\r\n'
            'Content-Length: 0\r\n'
            '\r\n' % method_
        ).encode('iso-8859-1')

    @staticmethod
    def parse(inbound, outbound, scheme=u'http'):
        exchanges = list(analyze_streams(inbound, outbound, scheme))
        text_report(exchanges, StringIO())
        html_report(exchanges, StringIO())
        return [exch.responses for exch in exchanges if exch.responses]

    def test_analyze_exchange(self):
        req = Request(u'http',
                      u'GET', u'/', u'HTTP/1.1',
                      [(u'Host', b'example.com')])
        self.assertEqual(repr(req), '<Request GET>')
        resp1 = Response(u'HTTP/1.1', 123, u'Please wait', [])
        self.assertEqual(repr(resp1), '<Response 123>')
        resp2 = Response(u'HTTP/1.1', 200, u'OK',
                         [(u'Content-Length', b'14')],
                         b'Hello world!\r\n')
        exch = analyze_exchange(Exchange(req, [resp1, resp2]))
        self.assertEqual(repr(exch),
                         'ExchangeView(<RequestView GET>, '
                         '[<ResponseView 123>, <ResponseView 200>])')
        self.assertTrue(isinstance(exch.request.method, Method))
        self.assertTrue(isinstance(exch.request.version, HTTPVersion))
        self.assertTrue(isinstance(exch.request.header_entries[0].name,
                                   FieldName))
        self.assertTrue(isinstance(exch.responses[0].version, HTTPVersion))
        self.assertTrue(isinstance(exch.responses[0].status, StatusCode))
        self.assertTrue(isinstance(exch.responses[1].header_entries[0].name,
                                   FieldName))

    def test_parse_responses(self):
        inbound = self.req(m.HEAD) + self.req(m.POST) + self.req(m.POST)
        stream = (b'HTTP/1.1 200 OK\r\n'
                  b'Content-Length: 16\r\n'
                  b'\r\n'
                  b'HTTP/1.1 100 Continue\r\n'
                  b'\r\n'
                  b"HTTP/1.1 100 Keep On Rollin' Baby\r\n"
                  b'\r\n'
                  b'HTTP/1.1 200 OK\r\n'
                  b'Content-Length: 16\r\n'
                  b'\r\n'
                  b'Hello world!\r\n'
                  b'\r\n'
                  b'HTTP/1.1 101 Switching Protocols\r\n'
                  b'Upgrade: wololo\r\n'
                  b'\r\n')
        [[resp1_1], [resp2_1, resp2_2, resp2_3], [resp3_1]] = \
            self.parse(inbound, stream)

        self.assertEqual(resp1_1.status, 200)
        self.assertEqual(repr(resp1_1.status), 'StatusCode(200)')
        self.assertEqual(resp1_1.headers.content_length.value, 16)
        self.assertIs(resp1_1.body, None)

        self.assertEqual(resp2_1.status, 100)
        self.assertEqual(resp2_1.reason, u'Continue')
        self.assertEqual(resp2_2.status, 100)
        self.assertEqual(resp2_2.reason, u"Keep On Rollin' Baby")
        self.assertEqual(resp2_3.status, 200)
        self.assertEqual(resp2_3.headers.content_length.value, 16)
        self.assertEqual(resp2_3.body, b'Hello world!\r\n\r\n')

        self.assertEqual(resp3_1.status, 101)
        self.assertEqual(resp3_1.header_entries[0].value, b'wololo')
        self.assertIs(resp3_1.body, None)

    def test_parse_responses_not_enough_requests(self):
        inbound = self.req(m.POST)
        stream = (b'HTTP/1.1 200 OK\r\n'
                  b'Content-Length: 16\r\n'
                  b'\r\n'
                  b'Hello world!\r\n'
                  b'\r\n'
                  b'HTTP/1.1 101 Switching Protocols\r\n'
                  b'\r\n')
        [[resp1], [resp2]] = self.parse(inbound, stream)
        self.assertEqual(resp1.body, b'Hello world!\r\n\r\n')
        self.assertEqual(resp2.status, 101)

    def test_parse_responses_bad_framing(self):
        self.assertEqual(self.parse(self.req(m.POST), b'HTTP/1.1 ...'), [])

    def test_parse_responses_implicit_framing(self):
        inbound = self.req(m.POST)
        stream = (b'HTTP/1.1 200 OK\r\n'
                  b'\r\n'
                  b'Hello world!\r\n')
        [[resp1]] = self.parse(inbound, stream)
        self.assertEqual(resp1.body, b'Hello world!\r\n')

    def test_warning(self):
        inbound = self.req(m.GET)
        stream = (b'HTTP/1.1 200 0K\r\n'
                  b'Content-Type: text/plain\r\n'
                  b'Warning: 123 - "something"\r\n'
                  b'Warning: 234 [::0]:8080 "something else"\r\n'
                  b'    "Thu, 28 Jan 2016 08:22:04 GMT" \r\n'
                  b'Warning: 345 - forgot to quote this one\r\n'
                  b'Warning: 456 baz "qux", 567 - "xyzzy"\r\n'
                  b'\r\n'
                  b'Hello world!\r\n')
        [[resp1]] = self.parse(inbound, stream)
        self.assertEqual(
            resp1.headers.warning.value,
            [WarningValue(WarnCode(123), u'-', u'something', None),
             WarningValue(WarnCode(234), u'[::0]:8080', u'something else',
                          datetime(2016, 1, 28, 8, 22, 4)),
             Unavailable,
             WarningValue(WarnCode(456), u'baz', u'qux', None),
             WarningValue(WarnCode(567), u'-', u'xyzzy', None)])
        self.assertEqual(repr(resp1.headers.warning.value[0].code),
                         'WarnCode(123)')
        self.assertIn(WarnCode(123), resp1.headers.warning)
        self.assertIn(WarnCode(567), resp1.headers.warning)
        self.assertNotIn(WarnCode(199), resp1.headers.warning)

    def test_www_authenticate(self):
        inbound = self.req(m.GET)
        stream = (b'HTTP/1.1 401 Unauthorized\r\n'
                  b'Content-Type: text/plain\r\n'
                  b'WWW-Authenticate: Basic realm="my \\"magical\\" realm"\r\n'
                  b'WWW-Authenticate: Foo  , Bar jgfCGSU8u== \r\n'
                  b'WWW-Authenticate: Baz\r\n'
                  b'WWW-Authenticate: Wrong=bad, Better\r\n'
                  b'WWW-Authenticate: scheme1 foo=bar, baz=qux, scheme2\r\n'
                  b'WWW-Authenticate: Newauth Realm="apps", type=1,\r\n'
                  b'    title="Login to \\"apps\\"",\r\n'
                  b'    Basic realm="simple"\r\n'
                  b'\r\n'
                  b'Hello world!\r\n')
        [[resp1]] = self.parse(inbound, stream)
        self.assertEqual(
            resp1.headers.www_authenticate.value,
            [
                Parametrized(AuthScheme(u'Basic'),
                             [(u'realm', u'my "magical" realm')]),
                Parametrized(AuthScheme(u'Foo'), None),
                Parametrized(AuthScheme(u'Bar'), u'jgfCGSU8u=='),
                Parametrized(AuthScheme(u'Baz'), None),
                Unavailable,
                Parametrized(AuthScheme(u'Scheme1'), [(u'foo', u'bar'),
                                                      (u'baz', u'qux')]),
                Parametrized(AuthScheme(u'Scheme2'), None),
                Parametrized(AuthScheme(u'Newauth'),
                             [(u'realm', u'apps'), (u'type', u'1'),
                              (u'title', u'Login to "apps"')]),
                Parametrized(AuthScheme(u'basic'), [(u'realm', u'simple')]),
            ]
        )

    def test_hsts(self):
        inbound = self.req(m.GET)
        stream = (b'HTTP/1.1 200 OK\r\n'
                  b'Content-Type: text/plain\r\n'
                  b'Strict-Transport-Security: foo\r\n'
                  b'Strict-Transport-Security: ;max-age  =  "15768000" ;\r\n'
                  b'     includeSubdomains=xyzzy; ; max-age;  foobar ;\r\n'
                  b'\r\n'
                  b'Hello world!\r\n')
        [[resp1]] = self.parse(inbound, stream)
        self.assertEqual(
            resp1.headers.strict_transport_security.value,
            [
                Parametrized(hsts.max_age, 15768000),
                Parametrized(hsts.includesubdomains, None),
                Parametrized(hsts.max_age, Unavailable),
                Parametrized(HSTSDirective(u'fooBar'), None),
            ]
        )
        self.assertEqual(
            resp1.headers.strict_transport_security.max_age, 15768000)
        self.assertEqual(
            resp1.headers.strict_transport_security.includesubdomains, True)

    def test_fuzz(self):
        # Make sure we don't raise exceptions even on very wrong inputs.
        interesting_headers = [hdr for hdr in h if header.parser_for(hdr)]
        rng_state = random.getstate()
        n_failed = 0
        for _ in range(20):
            req = Request(random.choice([u'http', u'https', u'foobar']),
                          random.choice(list(m)),
                          binary_garbage().decode('iso-8859-1'),
                          random.choice([http10, http11, u'HTTP/3.0']),
                          [HeaderEntry(random.choice(interesting_headers),
                                       make_header_value()) for _ in range(5)],
                          binary_garbage(),
                          [HeaderEntry(random.choice(interesting_headers),
                                       make_header_value())])
            resps = [Response(random.choice([http10, http11, u'HTTP/3.0']),
                              random.choice(list(st)),
                              binary_garbage().decode('iso-8859-1'),
                              [HeaderEntry(random.choice(interesting_headers),
                                           make_header_value())
                               for _ in range(5)],
                              binary_garbage(),
                              [HeaderEntry(random.choice(interesting_headers),
                                           make_header_value())])
                     for _ in range(random.randint(1, 3))]
            try:
                exch = analyze_exchange(Exchange(req, resps))
                text_report([exch], StringIO())
                html_report([exch], StringIO())
            except Exception as e:
                n_failed += 1
        if n_failed > 0:
            filename = 'fuzz-rng-state.pickle'
            with io.open(filename, 'wb') as outf:
                pickle.dump(rng_state, outf)
            self.fail(u'%d exchanges caused errors; '
                      u'RNG state dumped into %s' % (n_failed, filename))


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
        inb, outb, scheme, expected = load_test_file(filename)
        exchanges = list(analyze_streams(inb, outb, scheme))
        buf = StringIO()
        text_report(exchanges, buf)
        actual = sorted(int(ln[2:6]) for ln in buf.getvalue().splitlines()
                        if not ln.startswith(u'------------'))
        self.covered.update(actual)
        self.assertEqual(expected, actual)
        html_report(exchanges, StringIO())
        if self.examples is not None:
            for exch in exchanges:
                for ident, ctx in exch.collect_complaints():
                    self.examples.setdefault(ident, ctx)

    def test_all_notices_covered(self):
        self.assertEqual(self.covered, set(notices))
        if self.examples is not None:
            self.assertEqual(self.covered, set(self.examples))
            with io.open(self.examples_filename, 'wt', encoding='utf-8') as f:
                f.write(render_notice_examples(
                    (notices[ident], ctx)
                    for ident, ctx in sorted(self.examples.items())
                ))

TestFromFiles.load_tests()


if __name__ == '__main__':
    unittest.main()
