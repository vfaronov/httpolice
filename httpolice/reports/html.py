# -*- coding: utf-8; -*-

import codecs
import json

import dominate
import dominate.tags as H
import six

from httpolice import known, message, notice
from httpolice.citation import Citation
from httpolice.parse import ParseError
from httpolice.header import HeaderView
from httpolice.reports.common import (
    expand_parse_error,
    expand_piece,
    find_reason_phrase,
)
from httpolice.structure import Unavailable, okay
from httpolice.util.text import has_nonprintable, nicely_join, printable


def html_report(exchanges, outfile):
    document = dominate.document(title=u'HTTPolice report')
    with document.head:
        H.meta(http_equiv=u'Content-Type',
               content=u'text/html; charset=utf-8')
        _include_stylesheet()
        _include_scripts()
    with document:
        _render_exchanges(exchanges)
    outfile.write(document.render())


def render_notice_examples(examples):
    document = dominate.document(title=u'HTTPolice notice examples')
    with document.head:
        H.meta(http_equiv=u'Content-Type', content=u'text/html; charset=utf-8')
        _include_stylesheet()
    with document:
        H.h1(u'HTTPolice notice examples')
        with H.table(_class=u'notice-examples'):
            H.thead(H.tr(H.th(u'ID'), H.th(u'severity'), H.th(u'example')))
            with H.tbody():
                for the_notice, ctx in examples:
                    with H.tr():
                        H.td(six.text_type(the_notice.ident))
                        H.td(the_notice.severity)
                        with H.td():
                            _notice_to_html(the_notice, ctx, for_example=True)
    return document.render()


def _render_exchanges(exchanges):
    for exch in exchanges:
        with H.div(**_for_object(exch)):
            if exch.request:
                _render_request(exch.request)
            for resp in exch.responses:
                _render_response(resp)
            _render_complaints(exch)
            H.br(_class=u'item-separator')


def _render_complaints(obj):
    if obj.complaints:
        with H.div(_class=u'notices'):
            for complaint in obj.complaints:
                the_notice = notice.notices[complaint.notice_ident]
                _notice_to_html(the_notice, complaint.context)


def _render_annotated(pieces):
    for piece in pieces:
        with H.span(_class=u'annotated-piece', **_for_object(piece)):
            if isinstance(piece, bytes):
                H.span(printable(piece.decode('iso-8859-1')))
            else:
                _known_to_html(piece)


def _render_header_entries(annotated_entries):
    for entry, annotated in annotated_entries:
        with H.div(__inline=True, **_for_object(entry)):
            _known_to_html(entry.name)
            H.span(u': ')
            _render_annotated(annotated)


def _render_message(msg):
    _render_header_entries(msg.annotated_header_entries)

    body, transforms = _displayable_body(msg)
    if body is Unavailable:
        with H.div(_class=u'review-block'):
            H.p(u'Payload body is unavailable.', _class=u'hint')
    elif body:
        with H.div(**_for_object(msg.body, extra_class=u'review-block')):
            if transforms:
                H.p(u'Payload body after %s:' % nicely_join(transforms),
                    _class=u'hint')
            H.div(body, _class=u'payload-body')

    if msg.trailer_entries:
        with H.div(_class=u'review-block'):
            H.p(u'Header fields from the trailer part:', _class=u'hint')
            _render_header_entries(msg.annotated_trailer_entries)


def _render_request(req):
    with H.div(_class=u'review'):
        with H.div(_class=u'request-line', __inline=True):
            with H.span(**_for_object(req.method)):
                _known_to_html(req.method)
            H.span(u' ')
            H.span(printable(req.target),
                   **_for_object(req.target, u'request-target'))
            H.span(u' ')
            H.span(printable(req.version), **_for_object(req.version))
        _render_message(req)
    _render_complaints(req)


def _render_response(resp):
    with H.div(_class=u'review'):
        with H.div(_class=u'status-line', __inline=True):
            H.span(printable(resp.version), **_for_object(resp.version))
            H.span(u' ')
            with H.span(**_for_object(resp.status)):
                _known_to_html(resp.status)
                H.span(u' ')
                H.span(printable(find_reason_phrase(resp)))
        _render_message(resp)
    _render_complaints(resp)


def _include_stylesheet():
    H.link(rel=u'stylesheet', href=u'report.css', type=u'text/css')


def _include_scripts():
    H.script(src=u'https://code.jquery.com/jquery-1.11.3.js',
             type=u'text/javascript')
    H.script(src=u'report.js', type=u'text/javascript')


def _for_object(obj, extra_class=u''):
    assert okay(obj)
    return {
        u'class': u'%s %s' % (type(obj).__name__, extra_class),
        u'id': six.text_type(id(obj)),
    }


def _reference_targets(obj):
    if isinstance(obj, HeaderView):
        return [u'#' + six.text_type(id(entry)) for entry in obj.entries]
    elif isinstance(obj, list):
        # Support no. 1013, where we want to highlight all entries,
        # not just the one which is ultimately selected by `SingleHeaderView`.
        # Makes sense in general, so I'm inclined not to consider it a hack.
        return [ref for item in obj for ref in _reference_targets(item)]
    else:
        return [u'#' + six.text_type(id(obj))]


def _known_to_html(obj):
    cls = u'known known-%s' % type(obj).__name__
    text = printable(six.text_type(obj))
    cite = known.citation(obj)
    title = known.title(obj, with_citation=True)
    if cite:
        elem = H.a(text, _class=cls, href=cite.url, target=u'_blank')
    else:
        elem = H.span(text, _class=cls)
    if title:
        with elem:
            H.attr(title=title)


def _notice_to_html(the_notice, ctx, for_example=False):
    with H.div(_class=u'notice notice-%s' % the_notice.severity):
        with H.p(_class=u'notice-heading', __inline=True):
            if not for_example:
                with H.span(_class=u'notice-info'):
                    H.span(six.text_type(the_notice.ident),
                           _class=u'notice-ident')
                    H.span(u' ')
                    H.span(the_notice.severity_short,
                           _class=u'notice-severity',
                           title=the_notice.severity)
                H.span(u' ')
            with H.span(_class=u'notice-title'):
                _piece_to_html(the_notice.title, ctx)
        for para in the_notice.explanation:
            _piece_to_html(para, ctx)


def _piece_to_html(piece, ctx):
    if isinstance(piece, list):
        for p in piece:
            _piece_to_html(p, ctx)

    elif isinstance(piece, notice.Paragraph):
        with H.p(_class=u'notice-para', __inline=True):
            _piece_to_html(piece.content, ctx)

    elif isinstance(piece, notice.Ref):
        target = piece.resolve_reference(ctx)
        with H.span(data_ref_to=u', '.join(_reference_targets(target))):
            _piece_to_html(piece.content or target, ctx)

    elif isinstance(piece, notice.Cite):
        _piece_to_html(piece.info, ctx)
        quote = piece.content
        if quote:
            H.span(u': ')
            with H.q(cite=piece.info.url):
                _piece_to_html(quote, ctx)

    elif isinstance(piece, ParseError):
        for para in expand_parse_error(piece):
            with H.p(_class=u'notice-para', __inline=True):
                _piece_to_html(para, ctx)

    elif isinstance(piece, Citation):
        with H.cite():
            H.a(piece.title, href=piece.url, target=u'_blank')

    elif known.is_known(piece):
        _known_to_html(piece)

    elif isinstance(piece, six.text_type):
        H.span(printable(piece))

    else:
        _piece_to_html(expand_piece(piece), ctx)


def _displayable_body(msg):
    r = msg.body
    transforms = []
    if not okay(r):
        return r, transforms

    r = r.decode('utf-8', 'replace')
    if msg.headers.transfer_encoding:
        transforms.append(u'removing Transfer-Encoding')

    if okay(msg.decoded_body):
        r = msg.decoded_body.decode('utf-8', 'replace')
        if msg.headers.content_encoding:
            transforms.append(u'removing Content-Encoding')

    if okay(msg.json_data):
        r = json.dumps(msg.json_data, indent=2, ensure_ascii=False)
        transforms.append(u'pretty-printing')
    elif okay(msg.decoded_body):
        charset = message.body_charset(msg) or 'UTF-8'
        try:
            codec = codecs.lookup(charset)
        except LookupError:
            codec = codecs.lookup('utf-8')
        r = msg.decoded_body.decode(codec.name, 'replace')
        if codec.name != 'utf-8':
            transforms.append(u'decoding from %s' % charset)

    limit = 5000
    if len(r) > limit:
        r = r[:limit]
        transforms.append(u'taking the first %d characters' % limit)

    if has_nonprintable(r):
        transforms.append(u'replacing non-printable characters '
                          u'with the \ufffd sign')
        r = printable(r)

    return r, transforms
