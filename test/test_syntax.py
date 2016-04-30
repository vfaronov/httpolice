# -*- coding: utf-8; -*-

from datetime import datetime
import unittest

from httpolice import parse
from httpolice.known import cc, media, tc, unit
from httpolice.structure import (
    ContentCoding,
    ContentRange,
    ExtValue,
    LanguageTag,
    MediaType,
    MultiDict,
    Parametrized,
    ProductName,
    RangeSpecifier,
    RangeUnit,
    RelationType,
    TransferCoding,
    Unavailable,
    Versioned,
)
from httpolice.syntax import (
    rfc3986,
    rfc5988,
    rfc6266,
    rfc7230,
    rfc7231,
    rfc7233,
)


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
        self.assertParse(p, b'chunked', Parametrized(tc.chunked, MultiDict()))
        self.assertParse(p, b'foo',
                         Parametrized(TransferCoding(u'foo'), MultiDict()))
        self.assertParse(p, b'foo ; bar = baz ; qux = "\\"xyzzy\\""',
                         Parametrized(TransferCoding(u'foo'),
                                      MultiDict([(u'bar', u'baz'),
                                                 (u'qux', u'"xyzzy"')])))
        self.assertNoParse(p, b'')
        self.assertNoParse(p, b'foo;???')
        self.assertNoParse(p, b'foo;"bar"="baz"')

        p = rfc7230.t_codings
        self.assertParse(p, b'gzip;q=0.345',
                         Parametrized(Parametrized(tc.gzip, MultiDict()),
                                      0.345))
        self.assertParse(p, b'gzip; Q=1.0',
                         Parametrized(Parametrized(tc.gzip, MultiDict()),
                                      1))
        self.assertParse(p, b'trailers', u'trailers')
        self.assertNoParse(p, b'gzip;q=2.0')

    def test_media_type(self):
        p = rfc7231.media_type
        self.assertParse(
            p, b'Text/HTML; Charset="utf-8"',
            Parametrized(media.text_html, MultiDict([(u'charset', u'utf-8')])))
        self.assertParse(
            p, b'application/vnd.github.v3+json',
            Parametrized(MediaType(u'application/vnd.github.v3+json'),
                         MultiDict()))

    def test_accept(self):
        p = rfc7231.Accept
        self.assertParse(
            p,
            b'text/html;charset="utf-8";Q=1;profile="mobile", '
            b'text/plain;Q=0.2, text/*;Q=0.02, */*;Q=0.01',
            [
                Parametrized(
                    Parametrized(media.text_html,
                                 MultiDict([(u'charset', u'utf-8')])),
                    MultiDict([(u'q', 1), (u'profile', u'mobile')])
                ),
                Parametrized(
                    Parametrized(media.text_plain, MultiDict()),
                    MultiDict([(u'q', 0.2)])
                ),
                Parametrized(
                    Parametrized(MediaType(u'text/*'), MultiDict()),
                    MultiDict([(u'q', 0.02)])
                ),
                Parametrized(
                    Parametrized(MediaType(u'*/*'), MultiDict()),
                    MultiDict([(u'q', 0.01)])
                ),
            ]
        )
        self.assertParse(
            p, b'*/*',
            [Parametrized(Parametrized(MediaType(u'*/*'), MultiDict()),
                          MultiDict())])
        self.assertParse(
            p, b'application/json',
            [Parametrized(Parametrized(media.application_json, MultiDict()),
                          MultiDict())])
        self.assertParse(
            p, b'audio/*; q=0.2, audio/basic',
            [
                Parametrized(Parametrized(MediaType(u'audio/*'), MultiDict()),
                             MultiDict([(u'q', 0.2)])),
                Parametrized(Parametrized(media.audio_basic, MultiDict()),
                             MultiDict()),
            ])
        self.assertParse(
            p, b'text/plain; q=0.5, text/html, text/x-dvi; q=0.8, text/x-c',
            [
                Parametrized(Parametrized(media.text_plain, MultiDict()),
                             MultiDict([(u'q', 0.5)])),
                Parametrized(Parametrized(media.text_html, MultiDict()),
                             MultiDict()),
                Parametrized(Parametrized(MediaType(u'text/x-dvi'),
                                          MultiDict()),
                             MultiDict([(u'q', 0.8)])),
                Parametrized(Parametrized(MediaType(u'text/x-c'), MultiDict()),
                             MultiDict()),
            ])
        self.assertParse(
            p, b', ,text/*, text/plain,,, text/plain;format=flowed, */*',
            [
                Parametrized(Parametrized(MediaType(u'text/*'), MultiDict()),
                             MultiDict()),
                Parametrized(Parametrized(media.text_plain, MultiDict()),
                             MultiDict()),
                Parametrized(
                    Parametrized(media.text_plain,
                                 MultiDict([(u'format', u'flowed')])),
                    MultiDict()
                ),
                Parametrized(Parametrized(MediaType(u'*/*'), MultiDict()),
                             MultiDict()),
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
        self.assertParse(p, b'*', [Parametrized(u'*', None)])
        self.assertParse(
            p, b'compress;q=0.5, gzip;q=1.0',
            [Parametrized(cc.compress, 0.5), Parametrized(cc.gzip, 1)])
        self.assertParse(
            p, b'gzip;q=1.0, identity; q=0.5, *;q=0',
            [
                Parametrized(cc.gzip, 1),
                Parametrized(ContentCoding(u'identity'), 0.5),
                Parametrized(u'*', 0)
            ]
        )
        self.assertNoParse(p, b'gzip; identity')
        self.assertNoParse(p, b'gzip, q=1.0')

    def test_accept_language(self):
        p = rfc7231.Accept_Language
        self.assertParse(
            p, b'da, en-gb;q=0.8, en;q=0.7',
            [
                Parametrized(u'da', None),
                Parametrized(u'en-GB', 0.8),
                Parametrized(u'en', 0.7),
            ]
        )
        self.assertParse(p, b'en, *; q=0',
                         [Parametrized(u'en', None), Parametrized(u'*', 0)])
        self.assertParse(p, b'da', [Parametrized(u'da', None)])
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
                    MultiDict([
                        (u'rel', [RelationType(u'previous')]),
                        (u'title', u'previous chapter'),
                    ])
                )
            ],
        )
        self.assertParse(
            p, b'</>; rel="http://example.net/foo"',
            [Parametrized(u'/',
                          MultiDict([(u'rel', [u'http://example.net/foo'])]))]
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
                    MultiDict([
                        (u'rel', [RelationType(u'previous')]),
                        (u'title*',
                         ExtValue(u'UTF-8', u'de',
                                  u'letztes Kapitel'.encode('utf-8'))),
                    ])
                ),
                Parametrized(
                    u'/TheBook/chapter4',
                    MultiDict([
                        (u'rel', [RelationType(u'next')]),
                        (u'Title*',
                         ExtValue(u'UTF-8', u'de',
                                  u'nächstes Kapitel'.encode('utf-8'))),
                    ])
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
                    MultiDict([
                        (u'REL', [RelationType(u'START'),
                                  u'http://example.net/relation/other']),
                    ])
                ),
            ]
        )
        self.assertParse(
            p, b'</>; rel=foo; type=text/plain; rel=bar; type=text/html',
            [
                Parametrized(
                    u'/',
                    MultiDict([
                        (u'rel', [RelationType(u'foo')]),
                        (u'type', MediaType(u'text/plain')),
                        (u'type', MediaType(u'text/html')),
                    ])
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
                    MultiDict([
                        (u'media', u' whatever man okay?'),
                        (u'hreflang', LanguageTag(u'en-US')),
                    ])
                ),
            ]
        )
        self.assertParse(
            p, b'<foo>, <bar>, <>',
            [
                Parametrized(u'foo', MultiDict()),
                Parametrized(u'bar', MultiDict()),
                Parametrized(u'', MultiDict()),
            ]
        )
        self.assertParse(
            p, b"<urn:foo:bar:baz>; MyParam* = ISO-8859-1'en'whatever",
            [
                Parametrized(
                    u'urn:foo:bar:baz',
                    MultiDict([
                        (u'myparam*',
                         ExtValue(u'ISO-8859-1', u'en', b'whatever')),
                    ])
                ),
            ]
        )
        self.assertParse(
            p, b'<#me>; coolest; man; ever!',
            [
                Parametrized(
                    u'#me',
                    MultiDict([
                        (u'coolest', None),
                        (u'man', None),
                        (u'ever!', None),
                    ])
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

    def test_content_disposition(self):
        p = rfc6266.content_disposition
        self.assertParse(
            p, b'Attachment; filename=example.html',
            Parametrized(u'attachment',
                         MultiDict([(u'filename', u'example.html')]))
        )
        self.assertParse(
            p, b'INLINE; FILENAME= "an example.html"',
            Parametrized(u'inline',
                         MultiDict([(u'filename', u'an example.html')])))
        self.assertParse(
            p, b"attachment; filename*= UTF-8''%e2%82%ac%20rates",
            Parametrized(
                u'attachment',
                MultiDict([(u'filename*',
                            ExtValue(u'UTF-8', None,
                                     u'€ rates'.encode('utf-8')))])
            )
        )
        self.assertParse(
            p,
            b'attachment; filename="EURO rates"; '
            b"filename*=utf-8''%e2%82%ac%20rates",
            Parametrized(
                u'attachment',
                MultiDict([(u'filename', u'EURO rates'),
                           (u'filename*',
                            ExtValue(u'utf-8', None,
                                     u'€ rates'.encode('utf-8')))])
            )
        )
        self.assertNoParse(p, b'attachment; filename*=example.html')
