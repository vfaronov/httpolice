# -*- coding: utf-8; -*-

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
    context.out_filename = argv[1]
    context.pairs = []


def response(context, flow):
    req = httpolice.Request(flow.request.scheme,
                            flow.request.method, flow.request.path,
                            flow.request.http_version,
                            flow.request.headers.fields,
                            flow.request.content)
    preprocess_request(req)
    resp = httpolice.Response(req,
                              flow.response.http_version,
                              flow.response.status_code, flow.response.reason,
                              flow.response.headers.fields,
                              flow.response.content)
    preprocess_response(resp)
    context.pairs.append((req, resp))


def done(context):
    result = [httpolice.analyze_exchange(req, [resp])
              for req, resp in context.pairs]
    with open(context.out_filename, 'w') as outf:
        httpolice.HTMLReport.render(result, outf)
