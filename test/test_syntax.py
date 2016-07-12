# -*- coding: utf-8; -*-

from datetime import datetime

import pytest

from httpolice.known import cc, media, rel, tc, unit
from httpolice.parse import (ParseError, Stream, empty, literal, many, named,
                             recursive, skip, string, subst)
from httpolice.structure import (ContentRange, ExtValue, LanguageTag,
                                 MultiDict, Parametrized, RangeSpecifier,
                                 Unavailable, Versioned)
from httpolice.syntax import (rfc3986, rfc5988, rfc6266, rfc7230, rfc7231,
                              rfc7233)


def parse(parser, text):
    return Stream(text).parse(parser, to_eof=True)

def no_parse(parser, text):
    with pytest.raises(ParseError):
        parse(parser, text)


def test_parser_edge_cases():
    # Our parser implementation is general enough that
    # some of its branches are not being exercised by our regular tests,
    # so I had to come up with these contrived examples to test them.

    p = many(rfc7230.tchar)                            > named(u'p')
    p1 = '1' * p                                       > named(u'p1')
    p2 = '11' * p * skip('\n')                         > named(u'p2')
    assert parse(p1 | p2, b'11abc') == (u'1', [u'1', u'a', u'b', u'c'])
    assert parse(p1 | p2, b'11abc\n') == (u'11', [u'a', u'b', u'c'])

    p = recursive()                                    > named(u'p')
    p.rec = (rfc7230.tchar * p | subst(None) << empty)
    assert parse(p, b'abc') == (u'a', (u'b', (u'c', None)))

    p = literal('ab')                                  > named(u'p')
    p0 = subst(u'') << empty | p                       > named(u'p0')
    p1 = 'xab' * p0                                    > named(u'p1')
    p2 = 'x' * string(p0) * '!'                        > named(u'p2')
    assert parse(p1 | p2, b'xabab') == (u'xab', u'ab')
    assert parse(p1 | p2, b'xabab!') == (u'x', u'abab', u'!')

    p = empty | literal('a')                           > named(u'p')
    p0 = p * 'x'                                       > named(u'x')
    assert parse(p0, b'x') == u'x'


def test_comma_list():
    p = rfc7230.comma_list(rfc7230.token)
    assert parse(p, b'') == []
    assert parse(p, b', ,, , ,') == []
    assert parse(p, b'foo') == [u'foo']
    assert parse(p, b'foo,bar') == [u'foo', u'bar']
    assert parse(p, b'foo, bar,') == [u'foo', u'bar']
    assert parse(p, b', ,,,foo, ,bar, baz, ,, ,') == [u'foo', u'bar', u'baz']
    no_parse(p, b'foo,"bar"')
    no_parse(p, b'foo;bar')


def test_comma_list1():
    p = rfc7230.comma_list1(rfc7230.token)
    no_parse(p, b'')
    no_parse(p, b'  \t ')
    no_parse(p, b' , ,, , ,')
    assert parse(p, b'foo') == [u'foo']
    assert parse(p, b'foo,bar') == [u'foo', u'bar']
    assert parse(p, b'foo, bar,') == [u'foo', u'bar']
    assert parse(p, b', ,,,foo, ,bar, baz, ,, ,') == [u'foo', u'bar', u'baz']
    no_parse(p, b'foo,"bar"')
    no_parse(p, b'foo;bar')


def test_comment():
    p = rfc7230.comment(include_parens=False)
    assert parse(p, b'(foo (bar \\) baz "( qux)") xyzzy \\123 )') == \
        u'foo (bar ) baz "( qux)") xyzzy 123 '
    assert parse(p, u'(að láta (gera við) börn sín)'.encode('iso-8859-1')) == \
        u'að láta (gera við) börn sín'
    no_parse(p, b'(foo "bar)" baz)')


def test_transfer_coding():
    p = rfc7230.transfer_coding()
    assert parse(p, b'chunked') == Parametrized(tc.chunked, MultiDict())
    assert parse(p, b'foo') == Parametrized(u'foo', MultiDict())
    assert parse(p, b'foo ; bar = baz ; qux = "\\"xyzzy\\""') == \
        Parametrized(u'foo', MultiDict([(u'bar', u'baz'),
                                        (u'qux', u'"xyzzy"')]))
    no_parse(p, b'')
    no_parse(p, b'foo;???')
    no_parse(p, b'foo;"bar"="baz"')

    p = rfc7230.t_codings
    assert parse(p, b'gzip;q=0.345') == \
        Parametrized(Parametrized(tc.gzip, MultiDict()), 0.345)
    assert parse(p, b'gzip; Q=1.0') == \
        Parametrized(Parametrized(tc.gzip, MultiDict()), 1)
    assert parse(p, b'trailers') == u'trailers'
    no_parse(p, b'gzip;q=2.0')


def test_media_type():
    p = rfc7231.media_type
    assert parse(p, b'Text/HTML; Charset="utf-8"') == \
        Parametrized(media.text_html, MultiDict([(u'charset', u'utf-8')]))
    assert parse(p, b'application/vnd.github.v3+json') == \
        Parametrized(u'application/vnd.github.v3+json', MultiDict())


def test_accept():
    p = rfc7231.Accept

    assert parse(
        p,
        b'text/html;charset="utf-8";Q=1;profile="mobile", '
        b'text/plain;Q=0.2, text/*;Q=0.02, */*;Q=0.01'
    ) == [
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
                Parametrized(u'text/*', MultiDict()),
                MultiDict([(u'q', 0.02)])
            ),
            Parametrized(
                Parametrized(u'*/*', MultiDict()),
                MultiDict([(u'q', 0.01)])
            ),
        ]

    assert parse(p, b'*/*') == \
        [Parametrized(Parametrized(u'*/*', MultiDict()), MultiDict())]
    assert parse(p, b'application/json') == \
        [Parametrized(Parametrized(media.application_json, MultiDict()),
                      MultiDict())]
    assert parse(p, b'audio/*; q=0.2, audio/basic') == \
        [
            Parametrized(Parametrized(u'audio/*', MultiDict()),
                         MultiDict([(u'q', 0.2)])),
            Parametrized(Parametrized(media.audio_basic, MultiDict()),
                         MultiDict()),
        ]

    assert parse(
        p, b'text/plain; q=0.5, text/html, text/x-dvi; q=0.8, text/x-c'
    ) == [
            Parametrized(Parametrized(media.text_plain, MultiDict()),
                         MultiDict([(u'q', 0.5)])),
            Parametrized(Parametrized(media.text_html, MultiDict()),
                         MultiDict()),
            Parametrized(Parametrized(u'text/x-dvi', MultiDict()),
                         MultiDict([(u'q', 0.8)])),
            Parametrized(Parametrized(u'text/x-c', MultiDict()),
                         MultiDict()),
        ]

    assert parse(
        p, b', ,text/*, text/plain,,, text/plain;format=flowed, */*'
    ) == [
            Parametrized(Parametrized(u'text/*', MultiDict()),
                         MultiDict()),
            Parametrized(Parametrized(media.text_plain, MultiDict()),
                         MultiDict()),
            Parametrized(
                Parametrized(media.text_plain,
                             MultiDict([(u'format', u'flowed')])),
                MultiDict()
            ),
            Parametrized(Parametrized(u'*/*', MultiDict()),
                         MultiDict()),
        ]

    assert parse(p, b'') == []
    assert parse(p, b',') == []
    no_parse(p, b'text/html;q=foo-bar')
    no_parse(p, b'text/html;q=0.12345')
    no_parse(p, b'text/html;q=1.23456')
    no_parse(p, b'text/html;foo=bar;q=1.23456')
    no_parse(p, b'text/html=0.123')
    no_parse(p, b'text/html,q=0.123')
    no_parse(p, b'text/html q=0.123')
    no_parse(p, b'text/html;text/plain')
    no_parse(p, b'text/html;;q=0.123')
    no_parse(p, b'text/html;q="0.123"')


def test_accept_charset():
    p = rfc7231.Accept_Charset
    assert parse(p, b'iso-8859-5, unicode-1-1 ; q=0.8') == \
        [Parametrized(u'iso-8859-5', None), Parametrized(u'unicode-1-1', 0.8)]


def test_accept_encoding():
    p = rfc7231.Accept_Encoding
    assert parse(p, b'compress, gzip') == \
        [Parametrized(cc.compress, None), Parametrized(cc.gzip, None)]
    assert parse(p, b'') == []
    assert parse(p, b'*') == [Parametrized(u'*', None)]
    assert parse(p, b'compress;q=0.5, gzip;q=1.0') == \
        [Parametrized(cc.compress, 0.5), Parametrized(cc.gzip, 1)]
    assert parse(p, b'gzip;q=1.0, identity; q=0.5, *;q=0') == \
        [
            Parametrized(cc.gzip, 1),
            Parametrized(u'identity', 0.5),
            Parametrized(u'*', 0)
        ]
    no_parse(p, b'gzip; identity')
    no_parse(p, b'gzip, q=1.0')


def test_accept_language():
    p = rfc7231.Accept_Language
    assert parse(p, b'da, en-gb;q=0.8, en;q=0.7') == \
        [
            Parametrized(u'da', None),
            Parametrized(u'en-GB', 0.8),
            Parametrized(u'en', 0.7),
        ]
    assert parse(p, b'en, *; q=0') == \
        [Parametrized(u'en', None), Parametrized(u'*', 0)]
    assert parse(p, b'da') == [Parametrized(u'da', None)]
    no_parse(p, b'en_GB')
    no_parse(p, b'x1, x2')
    no_parse(p, b'en; q = 0.7')


def test_request_target():
    p = rfc7230.origin_form
    assert parse(p, b'/where?q=now')
    no_parse(p, b'/hello world')

    p = rfc7230.absolute_form
    assert parse(p, b'http://www.example.com:80')

    p = rfc7230.authority_form
    assert parse(p, b'www.example.com:80')
    assert parse(p, b'[::0]:8080')

    p = rfc7230.asterisk_form
    assert parse(p, b'*')

    p = rfc3986.absolute_URI
    assert parse(p, b'ftp://ftp.is.co.za/rfc/rfc1808.txt')
    assert parse(p, b'http://www.ietf.org/rfc/rfc2396.txt')
    assert parse(p, b'ldap://[2001:db8::7]/c=GB?objectClass?one')
    assert parse(p, b'mailto:John.Doe@example.com')
    assert parse(p, b'news:comp.infosystems.www.servers.unix')
    assert parse(p, b'tel:+1-816-555-1212')
    assert parse(p, b'telnet://192.0.2.16:80/')
    assert parse(p, b'urn:oasis:names:specification:docbook:dtd:xml:4.1.2')
    assert parse(p, b'http://[fe80::a%25en1]')      # RFC 6874


def test_partial_uri():
    p = rfc7230.partial_URI
    assert parse(p, b'/')
    assert parse(p, b'/foo/bar?baz=qux&xyzzy=123')
    assert parse(p, b'foo/bar/')
    assert parse(p, b'//example.net/static/ui.js')
    no_parse(p, b'/foo#bar=baz')


def test_via():
    p = rfc7230.Via
    assert parse(p, b'1.0 fred, 1.1 p.example.net') == \
        [
            (Versioned(u'HTTP', u'1.0'), u'fred', None),
            (Versioned(u'HTTP', u'1.1'), u'p.example.net', None)
        ]
    assert parse(
        p,
        br', FSTR/2 balancer4g-p1.example.com  '
        br'(Acme Web Accelerator 4.1 \(Debian\)), '
        br'1.1 proxy1,'
    ) == [
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
    no_parse(p, b'proxy1, proxy2')


def test_protocol():
    p = rfc7230.protocol
    assert parse(p, b'h2c') == (u'h2c', None)
    assert parse(p, b'FSTR/2') == (u'FSTR', u'2')
    no_parse(p, b'/2')


def test_user_agent():
    p = rfc7231.User_Agent
    assert parse(
        p,
        b'Mozilla/5.0 '
        b'(compatible; Vanadium '
        br'\(a nice browser btw, check us out: '
        br'http://vanadium.example/?about_us\)) '
        b'libVanadium/0.11a-pre9'
    ) == [
            Versioned(u'Mozilla', u'5.0'),
            u'compatible; Vanadium '
            u'(a nice browser btw, check us out: '
            u'http://vanadium.example/?about_us)',
            Versioned(u'libVanadium', u'0.11a-pre9'),
        ]

    assert parse(
        p,
        b'Mozilla/5.0 (X11; Linux x86_64) '
        b'AppleWebKit/537.36 (KHTML, like Gecko) '
        b'Chrome/37.0.2062.120 Safari/537.36'
    ) == [
            Versioned(u'Mozilla', u'5.0'),
            u'X11; Linux x86_64',
            Versioned(u'AppleWebKit', u'537.36'),
            u'KHTML, like Gecko',
            Versioned(u'Chrome', u'37.0.2062.120'),
            Versioned(u'Safari', u'537.36'),
        ]


def test_http_date():
    p = rfc7231.HTTP_date
    assert parse(p, b'Sun, 06 Nov 1994 08:49:37 GMT') == \
        datetime(1994, 11, 6, 8, 49, 37)
    assert parse(p, b'Sunday, 06-Nov-94 08:49:37 GMT') == \
        datetime(1994, 11, 6, 8, 49, 37)
    assert parse(p, b'Sun Nov  6 08:49:37 1994') == \
        datetime(1994, 11, 6, 8, 49, 37)
    assert parse(p, b'Sun Nov 16 08:49:37 1994') == \
        datetime(1994, 11, 16, 8, 49, 37)
    assert parse(p, b'Sun Nov 36 08:49:37 1994') is Unavailable
    assert parse(p, b'Sun Nov 16 28:49:37 1994') is Unavailable
    no_parse(p, b'Foo, 13 Jan 2016 24:09:06 GMT')


def test_acceptable_ranges():
    p = rfc7233.acceptable_ranges
    assert parse(p, b'none') == []
    assert parse(p, b'NONE') == []
    assert parse(p, b'none,') == [u'none']
    assert parse(p, b', ,Bytes, Pages') == [unit.bytes, u'pages']


def test_range():
    p = rfc7233.Range
    assert parse(p, b'bytes=0-499') == \
        RangeSpecifier(unit.bytes, [(0, 499)])
    assert parse(p, b'bytes=500-999') == \
        RangeSpecifier(unit.bytes, [(500, 999)])
    assert parse(p, b'bytes=9500-') == \
        RangeSpecifier(unit.bytes, [(9500, None)])
    assert parse(p, b'bytes=-500') == \
        RangeSpecifier(unit.bytes, [(None, 500)])
    assert parse(p, b'BYTES=0-0, -1') == \
        RangeSpecifier(unit.bytes, [(0, 0), (None, 1)])
    assert parse(p, b'Bytes=,500-700 ,601-999, ,') == \
        RangeSpecifier(unit.bytes, [(500, 700), (601, 999)])
    assert parse(p, b'pages=1-5') == \
        RangeSpecifier(u'pages', u'1-5')

    no_parse(p, b'bytes=1+2-3')
    no_parse(p, b'pages=1-5, 6-7')
    no_parse(p, b'1-5')


def test_content_range():
    p = rfc7233.Content_Range
    assert parse(p, b'bytes 42-1233/1234') == \
        ContentRange(unit.bytes, ((42, 1233), 1234))
    assert parse(p, b'bytes 42-1233/*') == \
        ContentRange(unit.bytes, ((42, 1233), None))
    assert parse(p, b'bytes */1234') == \
        ContentRange(unit.bytes, (None, 1234))
    assert parse(p, b'pages 1, 3, 5-7') == \
        ContentRange(u'pages', u'1, 3, 5-7')
    no_parse(p, b'bytes 42-1233')
    no_parse(p, b'bytes *')
    no_parse(p, b'bytes */*')
    no_parse(p, b'bytes 42/1233')
    no_parse(p, b'bytes 42, 43, 44')


def test_link():
    p = rfc5988.Link
    assert parse(
        p,
        b'<http://example.com/TheBook/chapter2>; rel="previous"; '
        b'title="previous chapter"'
    ) == [
            Parametrized(
                u'http://example.com/TheBook/chapter2',
                MultiDict([
                    (u'rel', [rel.previous]),
                    (u'title', u'previous chapter'),
                ])
            )
        ]

    assert parse(p, b'</>; rel="http://example.net/foo"') == \
        [Parametrized(u'/',
                      MultiDict([(u'rel', [u'http://example.net/foo'])]))]

    assert parse(
        p,
        b'</TheBook/chapter2>; '
        b'rel="previous"; title*=UTF-8\'de\'letztes%20Kapitel, '
        b'</TheBook/chapter4>; '
        b'rel="next"; title*=UTF-8\'de\'n%c3%a4chstes%20Kapitel'
    ) == [
            Parametrized(
                u'/TheBook/chapter2',
                MultiDict([
                    (u'rel', [rel.previous]),
                    (u'title*',
                     ExtValue(u'UTF-8', u'de',
                              u'letztes Kapitel'.encode('utf-8'))),
                ])
            ),
            Parametrized(
                u'/TheBook/chapter4',
                MultiDict([
                    (u'rel', [rel.next]),
                    (u'Title*',
                     ExtValue(u'UTF-8', u'de',
                              u'nächstes Kapitel'.encode('utf-8'))),
                ])
            ),
        ]

    assert parse(
        p,
        b'<http://example.org/>; '
        b'rel="start http://example.net/relation/other"'
    ) == [
            Parametrized(
                u'http://example.org/',
                MultiDict([
                    (u'REL', [u'START',
                              u'http://example.net/relation/other']),
                ])
            ),
        ]

    assert parse(
        p, b'</>; rel=foo; type=text/plain; rel=bar; type=text/html'
    ) == [
            Parametrized(
                u'/',
                MultiDict([
                    (u'rel', [u'foo']),
                    (u'type', media.text_plain),
                    (u'type', media.text_html),
                ])
            ),
        ]

    assert parse(
        p,
        b'</foo/bar?baz=qux#xyzzy>  ;  media = whatever man okay? ; '
        b'hreflang=en-US'
    ) == [
            Parametrized(
                u'/foo/bar?baz=qux#xyzzy',
                MultiDict([
                    (u'media', u' whatever man okay?'),
                    (u'hreflang', LanguageTag(u'en-US')),
                ])
            ),
        ]

    assert parse(p, b'<foo>, <bar>, <>') == \
        [
            Parametrized(u'foo', MultiDict()),
            Parametrized(u'bar', MultiDict()),
            Parametrized(u'', MultiDict()),
        ]

    assert parse(
        p, b"<urn:foo:bar:baz>; MyParam* = ISO-8859-1'en'whatever"
    ) == [
            Parametrized(
                u'urn:foo:bar:baz',
                MultiDict([
                    (u'myparam*',
                     ExtValue(u'ISO-8859-1', u'en', b'whatever')),
                ])
            ),
        ]

    assert parse(p, b'<#me>; coolest; man; ever!') == \
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

    no_parse(p, b'</>; anchor=/index.html')
    no_parse(p, u'<http://пример.рф/>; rel=next'.encode('utf-8'))
    no_parse(p, b'</index.html>; title=Hello')
    no_parse(p, b'</index.html>; type="text/html;charset=utf-8"')
    no_parse(p, b"</>; title * = UTF-8''Hello")
    no_parse(p, b'</index.html>;')
    no_parse(p, b'</index.html>; rel=next;')
    no_parse(p, b'</index.html>; foo*=bar')
    no_parse(p, b'</index.html>; hreflang="Hello world!"')


def test_content_disposition():
    p = rfc6266.content_disposition
    assert parse(p, b'Attachment; filename=example.html') == \
        Parametrized(u'attachment',
                     MultiDict([(u'filename', u'example.html')]))
    assert parse(p, b'INLINE; FILENAME= "an example.html"') == \
        Parametrized(u'inline',
                     MultiDict([(u'filename', u'an example.html')]))
    assert parse(p, b"attachment; filename*= UTF-8''%e2%82%ac%20rates") == \
        Parametrized(
            u'attachment',
            MultiDict([(u'filename*',
                        ExtValue(u'UTF-8', None,
                                 u'€ rates'.encode('utf-8')))])
        )
    assert parse(
        p,
        b'attachment; filename="EURO rates"; '
        b"filename*=utf-8''%e2%82%ac%20rates"
    ) == \
        Parametrized(
            u'attachment',
            MultiDict([(u'filename', u'EURO rates'),
                       (u'filename*',
                        ExtValue(u'utf-8', None,
                                 u'€ rates'.encode('utf-8')))])
        )
    no_parse(p, b'attachment; filename*=example.html')
