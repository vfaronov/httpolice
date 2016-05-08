# -*- coding: utf-8; -*-

import codecs
import re

from singledispatch import singledispatch
import six

from httpolice import notice
from httpolice.reports.common import (
    expand_error,
    expand_piece,
    find_reason_phrase,
    resolve_reference,
)
from httpolice.util.text import (
    detypographize,
    ellipsize,
    printable,
    write_if_any,
)


def text_report(exchanges, buf):
    """Generate a plain-text report with check results.

    :param exchanges:
        An iterable of :class:`~httpolice.Exchange` objects.
        They must be already processed by :func:`~httpolice.check_exchange`.

    :param buf:
        The file (or file-like object) to which the report will be written.
        It must be opened in binary mode (not text).

    """
    req_i = resp_i = 1
    f1 = codecs.getwriter('utf-8')(buf)
    for exch in exchanges:
        with write_if_any(_exchange_marker(exch, req_i), f1) as f2:
            if exch.request:
                req_i += 1
                for complaint in exch.request.complaints:
                    _write_complaint_line(complaint, f2)
            for resp in exch.responses:
                with write_if_any(_response_marker(resp, resp_i), f2) as f3:
                    resp_i += 1
                    for complaint in resp.complaints:
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
    return ellipsize(marker, 80) + u'\n'


def _response_marker(response, resp_i):
    return ellipsize(u'------------ response %d : %d %s' % (
                        resp_i,
                        response.status,
                        printable(find_reason_phrase(response)))) + u'\n'


def _write_complaint_line(complaint, f):
    the_notice = notice.notices[complaint.notice_id]
    title = detypographize(
        _piece_to_text(the_notice.title, complaint.context).strip())
    f.write(u'%s %d %s\n' % (the_notice.severity_short, the_notice.id, title))


@singledispatch
def _piece_to_text(piece, ctx):
    return _piece_to_text(expand_piece(piece), ctx)

@_piece_to_text.register(six.text_type)
def _text_to_text(text, _):
    return printable(text)

@_piece_to_text.register(list)
def _list_to_text(xs, ctx):
    return u''.join(_piece_to_text(x, ctx) for x in xs)

@_piece_to_text.register(notice.Paragraph)
def _para_to_text(para, ctx):
    return _piece_to_text(para.content, ctx) + u'\n'

@_piece_to_text.register(notice.Cite)
def _cite_to_text(cite, ctx):
    quote = cite.content
    if quote:
        quote = re.sub(u'\\s+', u' ', _piece_to_text(quote, ctx)).strip()
        return u'“%s” (%s)' % (quote, cite.info)
    else:
        return six.text_type(cite.info)

@_piece_to_text.register(notice.Var)
def _var_to_text(var, ctx):
    target = resolve_reference(ctx, var.reference)
    return _piece_to_text(target, ctx)

@_piece_to_text.register(notice.ExceptionDetails)
def _exc_to_text(_, ctx):
    return u''.join(_piece_to_text(para, ctx) + u'\n'
                    for para in expand_error(ctx['error']))

@_piece_to_text.register(notice.Ref)
def _ref_to_text(_ref, _ctx):
    return u''
