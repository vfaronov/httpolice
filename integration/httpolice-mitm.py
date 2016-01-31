# -*- coding: utf-8; -*-

import httpolice


def fix_headers(fields):
    # mitmproxy automatically adds a ``Content-Length`` header
    # to messages that lack it (because they have a ``Transfer-Encoding``).
    # HTTPolice doesn't want to see that.
    has_transfer_encoding = any(k.lower() == 'transfer-encoding'
                                for k, _ in fields)
    return [(k, v) for (k, v) in fields
            if k.lower() != 'content-length' or not has_transfer_encoding]


def start(context, argv):
    context.out_filename = argv[1]
    context.pairs = []


def response(context, flow):
    req = httpolice.Request(flow.request.scheme,
                            flow.request.method, flow.request.path,
                            flow.request.http_version,
                            fix_headers(flow.request.headers.fields),
                            flow.request.content)
    resp = httpolice.Response(req,
                              flow.response.http_version,
                              flow.response.status_code, flow.response.reason,
                              fix_headers(flow.response.headers.fields),
                              flow.response.content)
    context.pairs.append((req, resp))


def done(context):
    result = [httpolice.analyze_exchange(req, [resp])
              for req, resp in context.pairs]
    with open(context.out_filename, 'w') as outf:
        httpolice.HTMLReport.render(result, outf)
