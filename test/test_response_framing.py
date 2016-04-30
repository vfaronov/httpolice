# -*- coding: utf-8; -*-

from datetime import datetime
import unittest

import six

from httpolice.exchange import check_exchange
from httpolice.framing1 import parse_streams
from httpolice.known import altsvc, hsts, m
from httpolice.reports import html_report, text_report
from httpolice.structure import (
    AltSvcParam,
    AuthScheme,
    HSTSDirective,
    MultiDict,
    Parametrized,
    Unavailable,
    WarnCode,
    WarningValue,
)



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
        exchanges = list(parse_streams(inbound, outbound, scheme))
        for exch in exchanges:
            check_exchange(exch)
        text_report(exchanges, six.BytesIO())
        html_report(exchanges, six.BytesIO())
        return [exch.responses for exch in exchanges if exch.responses]

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
        self.assertEqual(resp1_1.body, b'')

        self.assertEqual(resp2_1.status, 100)
        self.assertEqual(resp2_1.reason, u'Continue')
        self.assertEqual(resp2_1.body, b'')
        self.assertEqual(resp2_2.status, 100)
        self.assertEqual(resp2_2.reason, u"Keep On Rollin' Baby")
        self.assertEqual(resp2_2.body, b'')
        self.assertEqual(resp2_3.status, 200)
        self.assertEqual(resp2_3.headers.content_length.value, 16)
        self.assertEqual(resp2_3.body, b'Hello world!\r\n\r\n')

        self.assertEqual(resp3_1.status, 101)
        self.assertEqual(resp3_1.header_entries[0].value, b'wololo')
        self.assertEqual(resp3_1.body, b'')

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
                             MultiDict([(u'realm', u'my "magical" realm')])),
                Parametrized(AuthScheme(u'Foo'), MultiDict()),
                Parametrized(AuthScheme(u'Bar'), u'jgfCGSU8u=='),
                Parametrized(AuthScheme(u'Baz'), MultiDict()),
                Unavailable,
                Parametrized(AuthScheme(u'Scheme1'),
                             MultiDict([(u'foo', u'bar'), (u'baz', u'qux')])),
                Parametrized(AuthScheme(u'Scheme2'), MultiDict()),
                Parametrized(AuthScheme(u'Newauth'),
                             MultiDict([(u'realm', u'apps'), (u'type', u'1'),
                                        (u'title', u'Login to "apps"')])),
                Parametrized(AuthScheme(u'basic'),
                             MultiDict([(u'realm', u'simple')])),
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

    def test_alt_svc(self):
        inbound = self.req(m.GET)

        stream = (b'HTTP/1.1 200 OK\r\n'
                  b'Alt-Svc: http%2F1.1="foo:443";ma=3600;persist=1 ,\r\n'
                  b'  h2=":8000";foo=bar\r\n'
                  b'\r\n')
        [[resp1]] = self.parse(inbound, stream)
        self.assertEqual(
            resp1.headers.alt_svc.value,
            [
                Parametrized(
                    (b'http/1.1', u'foo:443'),
                    MultiDict([(altsvc.ma, 3600), (altsvc.persist, True)])
                ),
                Parametrized(
                    (b'h2', u':8000'),
                    MultiDict([(AltSvcParam(u'foo'), u'bar')])
                ),
            ]
        )

        stream = (b'HTTP/1.1 200 OK\r\n'
                  b'Alt-Svc: clear\r\n'
                  b'\r\n')
        [[resp1]] = self.parse(inbound, stream)
        self.assertEqual(resp1.headers.alt_svc.value, u'clear')
