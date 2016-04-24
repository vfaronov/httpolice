# -*- coding: utf-8; -*-

from __future__ import absolute_import

import argparse
import io
import os

try:
    from httpolice import reports, Exchange, Request, Response, check_exchange
except ImportError:
    raise RuntimeError(
        'cannot load HTTPolice: '
        'did you install it in the same Python environment as mitmproxy?')

from httpolice.inputs.common import pop_pseudo_headers
from httpolice.known import h, st
from httpolice.structure import http2


def start(context, argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(u'-o', u'--output', choices=reports.formats,
                        default=u'text')
    parser.add_argument(u'report_filename')
    context.args = parser.parse_args(argv[1:])

    # Open the output file right now, because if it's wrong,
    # we don't want to wait until the end and lose all collected data.
    filename = os.path.expanduser(context.args.report_filename)
    context.report_file = io.open(filename, 'wb')

    context.exchanges = []


def response(context, flow):
    req = Request(flow.request.scheme,
                  flow.request.method, flow.request.path,
                  flow.request.http_version,
                  flow.request.headers.fields,
                  flow.request.content)
    preprocess_request(req)
    resp = Response(flow.response.http_version,
                    flow.response.status_code, flow.response.reason,
                    flow.response.headers.fields,
                    flow.response.content)
    preprocess_response(resp)
    exch = Exchange(req, [resp])
    check_exchange(exch)
    context.exchanges.append(exch)


def done(context):
    with context.report_file:
        report = reports.formats[context.args.output]
        report(context.exchanges, context.report_file)


def preprocess_request(req):
    preprocess_message(req)
    if req.version == http2:
        pseudo_headers = pop_pseudo_headers(req.header_entries)
        # Reconstruct HTTP/2's equivalent of
        # the "absolute form" of request target (RFC 7540 Section 8.1.2.3).
        if u':authority' in pseudo_headers and req.headers.host.is_absent:
            req.target = (req.scheme + u'://' + pseudo_headers[u':authority'] +
                          pseudo_headers[u':path'])


def preprocess_response(resp):
    preprocess_message(resp)
    pop_pseudo_headers(resp.header_entries)
    if resp.status.informational or resp.status in [st.no_content,
                                                    st.not_modified]:
        strip_content_length(resp, only_if=b'0')


def preprocess_message(msg):
    if msg.version == u'HTTP/2.0':
        msg.version = http2
    if any(entry.name == h.transfer_encoding for entry in msg.header_entries):
        strip_content_length(msg)


def strip_content_length(msg, only_if=None):
    # mitmproxy automatically adds a ``Content-Length`` header
    # to messages that lack it.
    # But some messages can't/shouldn't have a ``Content-Length`` at all.
    msg.header_entries = [
        e for e in msg.header_entries
        if e.name != h.content_length or (only_if and e.value != only_if)
    ]


if __name__ == '__main__':
    print(__file__)
