# -*- coding: utf-8; -*-

import httpolice


def start(context, argv):
    context.out_filename = argv[1]
    context.pairs = []


def response(context, flow):
    req = httpolice.Request(flow.request.scheme,
                            flow.request.method, flow.request.path,
                            flow.request.http_version,
                            flow.request.headers.fields,
                            flow.request.content or None)
    resp = httpolice.Response(req,
                              flow.response.http_version,
                              flow.response.status_code, flow.response.reason,
                              flow.response.headers.fields,
                              flow.response.content)
    context.pairs.append((req, resp))


def done(context):
    result = [httpolice.analyze_exchange(req, [resp])
              for req, resp in context.pairs]
    with open(context.out_filename, 'w') as outf:
        httpolice.HTMLReport.render(result, outf)
