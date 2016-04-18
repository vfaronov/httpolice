# -*- coding: utf-8; -*-

import argparse
import io

import httpolice
import httpolice.reports
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
    context.exchanges = []


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
    context.exchanges.append(httpolice.Exchange(req, [resp]))


def done(context):
    for exch in context.exchanges:
        httpolice.check_exchange(exch)
    if context.args.only_with_notices:
        context.exchanges = [exch for exch in context.exchanges
                             if any(exch.collect_complaints())]
    if context.args.html:
        report = httpolice.reports.html_report
    else:
        report = httpolice.reports.text_report
    with io.open(context.args.out_filename, 'wt', encoding='utf-8') as outf:
        report(context.exchanges, outf)
