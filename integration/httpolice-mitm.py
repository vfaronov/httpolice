# -*- coding: utf-8; -*-

import argparse
import io

import httpolice
from httpolice.known import h, st


def strip_content_length(msg, only_if=None):
    # mitmproxy automatically adds a ``Content-Length`` header
    # to messages that lack it.
    # But some messages can't/shouldn't have a ``Content-Length`` at all.
    msg.header_entries = [
        e for e in msg.header_entries
        if e.name != h.content_length or (only_if and e.value != only_if)
    ]


def preprocess_message(msg):
    if any(entry.name == h.transfer_encoding for entry in msg.header_entries):
        strip_content_length(msg)


def preprocess_request(req):
    preprocess_message(req)


def preprocess_response(resp):
    preprocess_message(resp)
    if resp.status.informational or \
            resp.status in [st.no_content, st.not_modified]:
        strip_content_length(resp, only_if='0')


def start(context, argv):
    parser = argparse.ArgumentParser(
        description=u'Run HTTPolice as a mitmdump script.',
        prog=u'httpolice-mitmdump.py')
    parser.add_argument(u'-H', u'--html', action=u'store_true',
                        help=u'render HTML report instead of plain text')
    parser.add_argument(u'--only-with-notices', action=u'store_true',
                        help=u'exclude exchanges that have no notices')
    parser.add_argument(u'out_filename')
    context.args = parser.parse_args(argv[1:])
    context.pairs = []


def response(context, flow):
    req = httpolice.Request(flow.request.scheme,
                            flow.request.method, flow.request.path,
                            flow.request.http_version,
                            flow.request.headers.fields,
                            flow.request.content)
    preprocess_request(req)
    resp = httpolice.Response(flow.response.http_version,
                              flow.response.status_code, flow.response.reason,
                              flow.response.headers.fields,
                              flow.response.content)
    preprocess_response(resp)
    context.pairs.append((req, resp))


def done(context):
    result = [httpolice.analyze_exchange(httpolice.Exchange(req, [resp]))
              for req, resp in context.pairs]
    if context.args.only_with_notices:
        result = [exch for exch in result if any(exch.collect_complaints())]
    if context.args.html:
        report_cls = httpolice.HTMLReport
    else:
        report_cls = httpolice.TextReport
    with io.open(context.args.out_filename, 'wt', encoding='utf-8') as outf:
        report_cls.render(result, outf)
