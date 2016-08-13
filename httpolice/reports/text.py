# -*- coding: utf-8; -*-

import codecs

from singledispatch import singledispatch
import six

from httpolice import notice
from httpolice.reports.common import (expand_piece, find_reason_phrase,
                                      resolve_reference)
from httpolice.util.text import (detypographize, ellipsize, printable,
                                 write_if_any)


def text_report(exchanges, buf):
    """Generate a plain-text report with check results.

    :param exchanges:
        An iterable of :class:`~httpolice.Exchange` objects.
        They must be already processed by :func:`~httpolice.check_exchange`.

    :param buf:
        The file (or file-like object) to which the report will be written.
        It must be opened in binary mode (not text).

    """
    f1 = codecs.getwriter('utf-8')(buf)
    for exch in exchanges:
        with write_if_any(_exchange_marker(exch), f1) as f2:
            if exch.request:
                for complaint in exch.request.complaints:
                    _write_complaint_line(complaint, f2)
            for resp in exch.responses:
                with write_if_any(_response_marker(resp), f2) as f3:
                    for complaint in resp.complaints:
                        _write_complaint_line(complaint, f3)
            for complaint in exch.complaints:
                _write_complaint_line(complaint, f2)


def _exchange_marker(exchange):
    if exchange.request:
        marker = u'------------ request: %s %s' % (
            printable(exchange.request.method),
            printable(exchange.request.target))
    elif exchange.responses:
        marker = u'------------ unknown request'
    else:
        marker = u'------------'
    # The number 79 fits the default ``cmd.exe`` size in Windows.
    return ellipsize(marker, 79) + u'\n'


def _response_marker(response):
    return ellipsize(u'------------ response: %d %s' % (
                        response.status,
                        printable(find_reason_phrase(response)))) + u'\n'


def _write_complaint_line(complaint, f):
    title = detypographize(
        _piece_to_text(complaint.notice.title, complaint.context).strip())
    f.write(u'%s %d %s\n' %
            (complaint.notice.severity_short, complaint.notice.id, title))


@singledispatch
def _piece_to_text(piece, ctx):
    return _piece_to_text(expand_piece(piece), ctx)

@_piece_to_text.register(six.text_type)
def _text_to_text(text, _):
    return printable(text)

@_piece_to_text.register(list)
def _list_to_text(xs, ctx):
    return u''.join(_piece_to_text(x, ctx) for x in xs)

@_piece_to_text.register(notice.Var)
def _var_to_text(var, ctx):
    target = resolve_reference(ctx, var.reference)
    return _piece_to_text(target, ctx)
