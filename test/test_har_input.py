# -*- coding: utf-8; -*-

import os

from httpolice.inputs.har import har_input
from httpolice.known import h, m
from httpolice.structure import Unavailable, http2, http11


def load_from_file(name):
    path = os.path.join(os.path.dirname(__file__), 'har_data', name)
    return list(har_input([path]))


def test_http2bin_chrome():
    exchanges = load_from_file('http2bin_chrome.har')

    assert u'http2bin_chrome.har' in exchanges[0].request.remark
    assert exchanges[0].request.version is None
    assert u'http2bin_chrome.har' in exchanges[0].responses[0].remark
    assert exchanges[0].responses[0].version is None
    assert exchanges[0].responses[0].body is Unavailable

    assert exchanges[1].request.target == u'https://http2bin.org/encoding/utf8'
    assert not exchanges[1].responses[0].reason

    assert exchanges[4].responses[0].body == b''

    assert exchanges[10].request.body is Unavailable
    assert exchanges[10].request.decoded_body is Unavailable
    assert exchanges[10].request.unicode_body == (u'custname=qwedqwed&'
                                                  u'custtel=dqwedwe&'
                                                  u'custemail=&'
                                                  u'size=medium&'
                                                  u'delivery=&'
                                                  u'comments=')


def test_http2bin_firefox():
    exchanges = load_from_file('http2bin_firefox.har')

    assert exchanges[0].request.version == http2
    assert exchanges[0].request.headers.connection.is_absent
    assert exchanges[0].responses[0].body is Unavailable
    assert exchanges[0].responses[0].decoded_body is Unavailable
    assert exchanges[0].responses[0].unicode_body[:5] == u'{\n  "'
    assert exchanges[0].responses[0].json_data['url'] == \
        u'https://http2bin.org/get'

    assert exchanges[5].responses[0].body == b''
    assert exchanges[5].responses[0].decoded_body == b''
    assert exchanges[5].responses[0].unicode_body == u''

    assert exchanges[7].responses[0].body is Unavailable
    assert len(exchanges[7].responses[0].decoded_body) == 1024

    assert exchanges[10].request.body is Unavailable
    assert exchanges[10].request.decoded_body is Unavailable
    assert exchanges[10].request.unicode_body == (u'custname=ferferf&'
                                                  u'custtel=rfwrefwerf&'
                                                  u'custemail=&'
                                                  u'size=medium&'
                                                  u'delivery=&'
                                                  u'comments=')


def test_spdy_chrome():
    exchanges = load_from_file('spdy_chrome.har')
    assert exchanges[0].request.version is None
    assert exchanges[0].responses[0].version is None
    assert exchanges[1].request.version is None
    assert exchanges[1].responses[0].version is None


def test_spdy_firefox():
    exchanges = load_from_file('spdy_firefox.har')
    assert exchanges[0].responses[0].version is None
    assert exchanges[1].responses[0].version is None


def test_xhr_chrome():
    exchanges = load_from_file('xhr_chrome.har')
    assert exchanges[0].request.target == u'/put'
    assert exchanges[0].request.version == http11
    assert exchanges[0].responses[0].version == http11
    assert exchanges[0].request.body is Unavailable
    assert exchanges[0].request.decoded_body is Unavailable
    assert exchanges[0].request.unicode_body == u'wrfqerfqerferg45rfrqerf'
    assert exchanges[0].responses[0].body is Unavailable
    assert exchanges[0].responses[0].decoded_body is Unavailable
    assert exchanges[0].responses[0].unicode_body[:5] == u'{\n  "'
    assert exchanges[0].responses[0].json_data['data'] == \
        u'wrfqerfqerferg45rfrqerf'


def test_xhr_firefox():
    exchanges = load_from_file('xhr_chrome.har')
    assert exchanges[0].request.target == u'/put'
    assert exchanges[0].request.version == http11
    assert exchanges[0].responses[0].version == http11


def test_httpbin_edge():
    exchanges = load_from_file('httpbin_edge.har')

    assert exchanges[0].request.target == u'/get'
    assert exchanges[0].request.version is None
    assert exchanges[0].responses[0].version is None
    assert exchanges[0].responses[0].body is Unavailable
    assert exchanges[0].responses[0].json_data['url'] == \
        u'http://httpbin.org/get'

    assert u'Unicode Demo' in exchanges[1].responses[0].unicode_body

    assert exchanges[4].responses[0].body == b''
    assert exchanges[5].responses[0].body == b''


def test_xhr_edge():
    exchanges = load_from_file('xhr_edge.har')
    assert exchanges[1].request.method == m.DELETE
    assert exchanges[1].request.body == b''
    assert exchanges[2].request.method == u'FOO-BAR'


def test_firefox_multiple_set_cookie():
    exchanges = load_from_file('firefox_set_cookie.har')
    [(_, _, (_, cookie1)), (_, _, (_, cookie2))] = \
        exchanges[0].responses[0].headers.enumerate(h.set_cookie)
    assert cookie1 == b'foo=bar'
    assert cookie2 == b'baz=qux'


def test_firefox_gif():
    exchanges = load_from_file('firefox_gif.har')
    assert exchanges[0].responses[0].body is Unavailable
    assert exchanges[0].responses[0].decoded_body is Unavailable


def test_fiddler_connect():
    exchanges = load_from_file('fiddler+ie11_connect.har')
    assert exchanges[0].request.target == u'httpbin.org:443'
    assert exchanges[0].request.body == b''
    assert exchanges[0].request.decoded_body == b''
    assert exchanges[0].responses[0].headers[u'StartTime'].is_present
    assert exchanges[0].responses[0].headers[u'EndTime'].is_absent
    assert exchanges[0].responses[0].body == b''
    assert exchanges[0].responses[0].decoded_body == b''
