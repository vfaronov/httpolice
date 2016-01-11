# -*- coding: utf-8; -*-

import httpolice.common
import httpolice.connection
import httpolice.report
import httpolice.request
import httpolice.response


def start(context, argv):
    context.out_filename = argv[1]
    context.conns = []


def response(context, flow):
    req = httpolice.request.Request(
        httpolice.common.Method(flow.request.method),
        flow.request.path,
        httpolice.common.HTTPVersion(flow.request.http_version),
        [httpolice.common.HeaderEntry(httpolice.common.FieldName(k), v)
         for k, v in flow.request.headers.fields],
        flow.request.content or None,
    )
    resp = httpolice.response.Response(
        httpolice.common.HTTPVersion(flow.response.http_version),
        httpolice.common.StatusCode(flow.response.status_code),
        reason=flow.response.reason,
        header_entries=[
            httpolice.common.HeaderEntry(httpolice.common.FieldName(k), v)
            for k, v in flow.response.headers.fields
        ],
        body=flow.response.content,
    )
    exch = httpolice.connection.Exchange(req, [resp])
    conn = httpolice.connection.Connection([exch])
    context.conns.append(conn)


def done(context):
    for conn in context.conns:
        httpolice.connection.check_connection(conn)
    with open(context.out_filename, 'w') as outf:
        httpolice.report.HTMLReport(outf).render_all(context.conns)
