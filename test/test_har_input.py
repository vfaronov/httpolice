# -*- coding: utf-8; -*-

import os
import unittest

from httpolice.inputs.har import har_input
from httpolice.structure import Unavailable, http11, http2


def load_from_file(name):
    path = os.path.join(os.path.dirname(__file__), 'har_data', name)
    return list(har_input([path]))


class TestHARInput(unittest.TestCase):

    def test_http2bin_chrome(self):
        exchanges = load_from_file('http2bin_chrome.har')

        self.assertIs(exchanges[0].request.version, None)
        self.assertIs(exchanges[0].responses[0].version, None)
        self.assertIs(exchanges[0].responses[0].body, Unavailable)

        self.assertEqual(exchanges[1].request.target,
                         u'https://http2bin.org/encoding/utf8')
        self.assertFalse(exchanges[1].responses[0].reason)

        self.assertIs(exchanges[10].request.body, Unavailable)
        self.assertIs(exchanges[10].request.decoded_body, Unavailable)
        self.assertEqual(exchanges[10].request.unicode_body,
                         u'custname=qwedqwed&'
                         u'custtel=dqwedwe&'
                         u'custemail=&'
                         u'size=medium&'
                         u'delivery=&'
                         u'comments=')

    def test_http2bin_firefox(self):
        exchanges = load_from_file('http2bin_firefox.har')

        self.assertEqual(exchanges[0].request.version, http2)
        self.assertIs(exchanges[0].responses[0].body, Unavailable)
        self.assertIs(exchanges[0].responses[0].decoded_body, Unavailable)
        self.assertEqual(exchanges[0].responses[0].unicode_body[:5],
                         u'{\n  "')
        self.assertEqual(exchanges[0].responses[0].json_data['url'],
                         u'https://http2bin.org/get')

        self.assertIs(exchanges[5].responses[0].body, None)
        self.assertIs(exchanges[5].responses[0].decoded_body, None)
        self.assertIs(exchanges[5].responses[0].unicode_body, None)

        self.assertIs(exchanges[7].responses[0].body, Unavailable)
        self.assertEqual(len(exchanges[7].responses[0].decoded_body), 1024)

        self.assertIs(exchanges[10].request.body, Unavailable)
        self.assertIs(exchanges[10].request.decoded_body, Unavailable)
        self.assertEqual(exchanges[10].request.unicode_body,
                         u'custname=ferferf&'
                         u'custtel=rfwrefwerf&'
                         u'custemail=&'
                         u'size=medium&'
                         u'delivery=&'
                         u'comments=')

    def test_spdy_chrome(self):
        exchanges = load_from_file('spdy_chrome.har')
        self.assertIs(exchanges[0].request.version, None)
        self.assertIs(exchanges[0].responses[0].version, None)
        self.assertIs(exchanges[1].request.version, None)
        self.assertIs(exchanges[1].responses[0].version, None)

    def test_spdy_firefox(self):
        exchanges = load_from_file('spdy_firefox.har')
        self.assertIs(exchanges[0].responses[0].version, None)
        self.assertIs(exchanges[1].responses[0].version, None)

    def test_xhr_chrome(self):
        exchanges = load_from_file('xhr_chrome.har')
        self.assertEqual(exchanges[0].request.target, u'/put')
        self.assertEqual(exchanges[0].request.version, http11)
        self.assertEqual(exchanges[0].responses[0].version, http11)
        self.assertIs(exchanges[0].request.body, Unavailable)
        self.assertIs(exchanges[0].request.decoded_body, Unavailable)
        self.assertEqual(exchanges[0].request.unicode_body,
                         u'wrfqerfqerferg45rfrqerf')
        self.assertIs(exchanges[0].responses[0].body, Unavailable)
        self.assertIs(exchanges[0].responses[0].decoded_body, Unavailable)
        self.assertEqual(exchanges[0].responses[0].unicode_body[:5],
                         u'{\n  "')
        self.assertEqual(exchanges[0].responses[0].json_data['data'],
                         u'wrfqerfqerferg45rfrqerf')

    def test_xhr_firefox(self):
        exchanges = load_from_file('xhr_chrome.har')
        self.assertEqual(exchanges[0].request.target, u'/put')
        self.assertEqual(exchanges[0].request.version, http11)
        self.assertEqual(exchanges[0].responses[0].version, http11)
