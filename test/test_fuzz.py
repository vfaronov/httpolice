# -*- coding: utf-8; -*-

"""Fuzz testing.

Generate random, very wrong inputs, and run them through HTTPolice.
We don't care about the results, but there must be no exceptions raised.
If there is, the state of the random generator is dumped
into a file with a ``.pickle`` suffix (in the current directory).
Then, the problem can be reproduced manually like this::

  import pickle, random, test_fuzz
  state = pickle.load(open('fuzz-state-XX.pickle', 'rb'))
  test_fuzz.test_fuzz(0, state)

"""

import io
import pickle
import random
import string

import pytest
import six

from httpolice import Exchange, Request, Response, check_exchange
from httpolice.known import h, header, m
from httpolice.reports import html_report, text_report
from httpolice.structure import http2, http10, http11


N_TESTS = 50

schemes = [u'http', u'https', u'foobar', None]
versions = [http10, http11, http2, u'HTTP/3.0', None]
methods = sorted(m)
header_names = sorted(hdr for hdr in h if header.parser_for(hdr) is not None)

def make_request_target():
    fuzzer = random.choice([make_token, make_garbage])
    prefix = random.choice([u'', u'/', u'http://', u'http://example.com/'])
    return prefix + fuzzer().decode('iso-8859-1')

def make_status_code():
    return random.randint(0, 700)

def make_reason_phrase():
    return random.choice([None, make_garbage().decode('iso-8859-1')])

def make_headers(max_num):
    return [(random.choice(header_names), make_header_value())
            for _ in range(random.randint(0, max_num))]

def make_header_value():
    fuzzers = [make_token, make_garbage,
               lambda: b',', lambda: b'"', lambda: b'']
    return b' '.join(random.choice(fuzzers)()
                     for _ in range(random.randint(0, 10)))

def make_body():
    return random.choice([b'', make_garbage()])

def make_token():
    return ''.join(random.choice(string.ascii_letters + string.digits)
                   for _ in range(random.randint(1, 10))).encode('ascii')

def make_garbage():
    return b''.join(six.int2byte(random.randint(0, 255))
                    for _ in range(10, 100))


@pytest.mark.parametrize('i', range(N_TESTS))
def test_fuzz(i, state=None):
    if state is None:
        state = random.getstate()
    else:
        random.setstate(state)

    req = random.choice([
        None,
        Request(random.choice(schemes),
                random.choice(methods),
                make_request_target(),
                random.choice(versions),
                make_headers(max_num=5),
                make_body(),
                make_headers(max_num=2))
    ])
    resps = [
        Response(random.choice(versions),
                 make_status_code(),
                 make_reason_phrase(),
                 make_headers(max_num=5),
                 make_body(),
                 make_headers(max_num=2))
        for _ in range(random.randint(0, 2))
    ]

    try:
        exch = Exchange(req, resps)
        check_exchange(exch)
        text_report([exch], six.BytesIO())
        html_report([exch], six.BytesIO())
    except Exception:
        filename = 'fuzz-state-%02d.pickle' % i
        with io.open(filename, 'wb') as f:
            pickle.dump(state, f)
        raise
