# -*- coding: utf-8; -*-

import re

import six

from httpolice import notice
from httpolice.reports.common import (
    expand_error,
    expand_piece,
    find_reason_phrase,
)
from httpolice.util.text import ellipsize, printable, write_if_any


def text_report(exchanges, outfile):
    req_i = resp_i = 1
    for exch in exchanges:
        with write_if_any(_exchange_marker(exch, req_i), outfile) as f2:
            if exch.request:
                req_i += 1
                for complaint in exch.request.collect_complaints():
                    _write_complaint_line(complaint, f2)
            for resp in exch.responses:
                with write_if_any(_response_marker(resp, resp_i), f2) as f3:
                    resp_i += 1
                    for complaint in resp.collect_complaints():
                        _write_complaint_line(complaint, f3)
            for complaint in exch.complaints:
                _write_complaint_line(complaint, f2)


def _exchange_marker(exchange, req_i):
    if exchange.request:
        marker = u'------------ request %d : %s %s' % (
            req_i,
            printable(exchange.request.method),
            printable(exchange.request.target))
    elif exchange.responses:
        marker = u'------------ unknown request'
    else:
        marker = u'------------'
    return ellipsize(marker) + u'\n'


def _response_marker(response, resp_i):
    return ellipsize(u'------------ response %d : %d %s' % (
                        resp_i,
                        response.status,
                        printable(find_reason_phrase(response)))) + u'\n'


def _write_complaint_line(complaint, f):
    the_notice = notice.notices[complaint.notice_ident]
    title = _piece_to_text(the_notice.title, complaint.context).strip()
    f.write(u'%s %d %s\n' % (the_notice.severity_short, the_notice.ident,
                             title))


def _piece_to_text(piece, ctx):
    if isinstance(piece, list):
        return u''.join(_piece_to_text(p, ctx) for p in piece)

    elif isinstance(piece, notice.Paragraph):
        return _piece_to_text(piece.content, ctx) + u'\n'

    elif isinstance(piece, notice.Ref):
        target = piece.resolve_reference(ctx)
        return _piece_to_text(piece.content or target, ctx)

    elif isinstance(piece, notice.Cite):
        quote = piece.content
        if quote:
            quote = re.sub(u'\\s+', u' ', _piece_to_text(quote, ctx)).strip()
            return u'“%s” (%s)' % (quote, piece.info)
        else:
            return six.text_type(piece.info)

    elif isinstance(piece, Exception):
        return u''.join(_piece_to_text(para, ctx) + u'\n'
                        for para in expand_error(piece))

    elif isinstance(piece, six.text_type):
        return printable(piece)

    else:
        return _piece_to_text(expand_piece(piece), ctx)
