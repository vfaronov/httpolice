# -*- coding: utf-8; -*-

"""Fuzz testing.

Generate random, very wrong inputs, and run them through HTTPolice.
We don't care about the results, but there must be no exceptions raised.
Inputs (and thus results) are deterministic within a given combination of:

1. Python version;
2. set of methods that HTTPolice knows;
3. set of headers that HTTPolice knows how to parse

(so, if you add a new header, you can suddenly discover unrelated bugs).
"""

import random
import string

import pytest
import six

from httpolice import Exchange, Request, Response, check_exchange
from httpolice.known import h, header, m
from httpolice.reports import html_report, text_report
from httpolice.structure import http2, http10, http11


N_TESTS = 100

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
    inner = random.choice([make_token] * 8 + [make_header_value, make_garbage])
    joiner = random.choice([b',', b';', b'=', b'/', b' '])
    return joiner.join(inner() for _ in range(random.randint(0, 3)))

def make_body():
    return random.choice([b'', make_garbage()])

def make_token():
    return ''.join(random.choice(string.ascii_letters + string.digits)
                   for _ in range(random.randint(1, 10))).encode('ascii')

def make_garbage():
    return b''.join(six.int2byte(random.randint(0, 255))
                    for _ in range(10, 100))

def make_exchange():
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
    return Exchange(req, resps)


@pytest.mark.parametrize('i', range(N_TESTS))
def test_fuzz(i):
    orig_state = random.getstate()
    random.seed(123456789 + i)      # Some arbitrary, but deterministic number.
    exch = make_exchange()
    random.setstate(orig_state)

    check_exchange(exch)
    text_report([exch], six.BytesIO())
    html_report([exch], six.BytesIO())
