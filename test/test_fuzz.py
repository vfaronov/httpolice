# -*- coding: utf-8; -*-

# Make sure we don't fail even on very wrong inputs.

import io
import pickle
import random
import string
import unittest

import six

from httpolice import Exchange, Request, Response, check_exchange
from httpolice.known import h, header, m
from httpolice.structure import http10, http11, http2
from httpolice.reports import html_report, text_report


interesting_headers = sorted(hdr for hdr in h if header.parser_for(hdr))

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



class TestFuzz(unittest.TestCase):

    def _run_fuzz(self, i):
        state = random.getstate()
        req = Request(
            scheme=random.choice([u'http', u'https', u'foobar', None]),
            method=random.choice(sorted(m)),
            target=binary_garbage().decode('iso-8859-1'),
            version=random.choice([http10, http11, http2, u'HTTP/3.0', None]),
            header_entries=[
                (random.choice(interesting_headers), make_header_value())
                for _ in range(5)
            ],
            body=random.choice([binary_garbage(), None]),
            trailer_entries=[
                (random.choice(interesting_headers), make_header_value())
            ],
        )
        resps = [
            Response(
                version=random.choice([http10, http11, http2,
                                       u'HTTP/3.0', None]),
                status=random.randint(0, 699),
                reason=binary_garbage().decode('iso-8859-1'),
                header_entries=[
                    (random.choice(interesting_headers), make_header_value())
                    for _ in range(5)
                ],
                body=random.choice([binary_garbage(), None]),
                trailer_entries=[
                    (random.choice(interesting_headers), make_header_value())
                ],
            )
            for _ in range(random.randint(1, 3))
        ]
        try:
            exch = Exchange(req, resps)
            check_exchange(exch)
            text_report([exch], six.BytesIO())
            html_report([exch], six.BytesIO())
        except Exception:
            # Dump the state of the random generator,
            # so that the problem can be reproduced.
            filename = 'test_fuzz_%02d_state.pickle' % i
            with io.open(filename, 'wb') as f:
                pickle.dump(state, f)
            raise

    def _make_case(i):
        def test_fuzz(self):
            self._run_fuzz(i)
        return test_fuzz

    for i in range(20):
        locals()['test_fuzz_%02d' % i] = _make_case(i)
