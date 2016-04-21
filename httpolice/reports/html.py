# -*- coding: utf-8; -*-

import json

import dominate
import dominate.tags as H
import pkg_resources
import six

from httpolice import known, message, notice, structure
from httpolice.__metadata__ import version
from httpolice.citation import Citation
from httpolice.header import HeaderView
from httpolice.reports.common import (
    expand_error,
    expand_piece,
    find_reason_phrase,
    resolve_reference,
)
from httpolice.structure import Unavailable, okay
from httpolice.util.text import nicely_join, printable


css_code = pkg_resources.resource_string('httpolice.reports', 'html.css'). \
    decode('utf-8')
js_code = pkg_resources.resource_string('httpolice.reports', 'html.js'). \
    decode('utf-8')


def html_report(exchanges, buf):
    title = u'HTTPolice report'
    document = dominate.document(title=title)
    with document.head:
        _common_meta()
        H.script(type=u'text/javascript').add_raw_string(js_code)
    with document:
        H.h1(title)
        _render_exchanges(exchanges)
    buf.write(document.render().encode('utf-8'))


class Placeholder(object):

    def __init__(self, name=None):
        self.name = name

    def get(self, name, _=None):
        return Placeholder(name)

    def __getitem__(self, name):
        return self.get(name)

    def __getattr__(self, name):
        return self.get(name)


def list_notices(buf):
    title = u'HTTPolice notices'
    document = dominate.document(title=title)
    with document.head:
        _common_meta()
    with document:
        H.h1(title)
        with H.div(_class=u'notices-list'):
            placeholder = Placeholder()
            for ident in sorted(notice.notices.keys()):
                _notice_to_html(notice.notices[ident], placeholder)
    buf.write(document.render().encode('utf-8'))


def _common_meta():
    H.meta(charset=u'utf-8')
    H.meta(name=u'generator', content=u'HTTPolice %s' % version)
    H.style(type=u'text/css').add_raw_string(css_code)


def _render_exchanges(exchanges):
    for exch in exchanges:
        with H.div(_class=u'exchange'):
            # The ``hr`` elements really help readability in w3m.
            if exch.request:
                _render_request(exch.request)
                H.hr()
            for resp in exch.responses:
                _render_response(resp)
                H.hr()
            if exch.complaints:
                _render_complaints(exch)
                H.hr()


def _render_request(req):
    with H.section():
        with H.div(_class=u'message-display'):
            with H.h2(), H.code():      # Request line
                # We don't insert spaces here because we assume that
                # Dominate will render each element on its own line,
                # thus implicitly creating whitespace.
                # https://github.com/Knio/dominate/issues/68
                with H.span(**_for_object(req.method)):
                    _known_to_html(req.method)
                H.span(printable(req.target), **_for_object(req.target))
                if req.version:
                    H.span(printable(req.version), **_for_object(req.version))
            _render_message(req)        # Headers, body and all that
        _render_complaints(req)


def _render_response(resp):
    with H.section():
        with H.div(_class=u'message-display'):
            with H.h2(), H.code():      # Status line
                # See above regarding spaces.
                if resp.version:
                    H.span(printable(resp.version),
                           **_for_object(resp.version))
                with H.span(**_for_object(resp.status)):
                    _known_to_html(resp.status)
                    H.span(printable(find_reason_phrase(resp)))
            _render_message(resp)       # Headers, body and all that
        _render_complaints(resp)


def _render_message(msg):
    _render_header_entries(msg.annotated_header_entries)

    body, transforms = _displayable_body(msg)
    if body != u'':
        with H.div(**_for_object(msg.body, u'body-display')):
            if body is None:
                H.h3(u'Body is unknown')
            elif body is Unavailable:
                H.h3(u'Body is present, but not available for inspection')
            else:
                if transforms:
                    H.h3(u'Body after %s' % nicely_join(transforms))
                H.pre(body)

    if msg.trailer_entries:
        with H.div(_class=u'trailer'):
            H.h3(u'Headers from the trailer part')
            _render_header_entries(msg.annotated_trailer_entries)


def _render_header_entries(annotated_entries):
    for entry, annotated in annotated_entries:
        with H.pre(**_for_object(entry, 'header-entry')), H.code():
            # Dominate (at least as of 2.2.0)
            # automatically inlines all descendants of ``pre``.
            # https://github.com/Knio/dominate/issues/68
            _known_to_html(entry.name)
            H.span(u': ')
            _render_annotated(annotated)


def _render_annotated(pieces):
    for piece in pieces:
        if isinstance(piece, bytes):
            H.span(printable(piece.decode('iso-8859-1')))
        else:
            with H.span(**_for_object(piece)):
                _known_to_html(piece)


def _render_complaints(obj):
    if obj.complaints:
        with H.div(_class=u'complaints'):
            for complaint in obj.complaints:
                the_notice = notice.notices[complaint.notice_ident]
                _notice_to_html(the_notice, complaint.context)


_seen_ids = {}


def _anonymize_id(id_):
    if id_ not in _seen_ids:
        _seen_ids[id_] = len(_seen_ids)
    return _seen_ids[id_]


def _reference_ids(obj):
    if isinstance(obj, list):
        return [ref for item in obj for ref in _reference_ids(item)]
    elif isinstance(obj, HeaderView):
        return [ref for entry in obj.entries for ref in _reference_ids(entry)]
    else:
        return [six.text_type(_anonymize_id(id(obj)))]


def _for_object(obj, extra_class=None):
    r = {u'data-ref-id': _reference_ids(obj)[0]}
    if extra_class:
        r[u'class'] = extra_class
    return r


def _referring_to(obj):
    return {u'data-ref-to': u' '.join(_reference_ids(obj))}


def _magic_references(elem, ctx):
    if elem.get('ref') == u'no':
        return []
    obj = elem.content
    msg = ctx.get('msg')
    if not isinstance(msg, message.Message):
        return []

    if isinstance(obj, structure.FieldName) and msg.headers[obj].is_present:
        return [msg.headers[obj]]

    if isinstance(obj, structure.Method):
        if getattr(msg, 'method', None) == obj:
            return [msg.method]
        if getattr(msg, 'request', None) and msg.request.method == obj:
            return [msg.request.method]

    if isinstance(obj, structure.StatusCode):
        if getattr(msg, 'status', None) == obj:
            return [msg.status]

    return []


def _known_to_html(obj):
    cls = type(obj).__name__
    text = printable(six.text_type(obj))
    cite = known.citation(obj)
    if cite:
        elem = H.a(text, _class=cls, href=cite.url, target=u'_blank',
                   __inline=True)
    else:
        elem = H.span(text, _class=cls, __inline=True)
    title = known.title(obj, with_citation=True)
    if title:
        with elem:
            H.attr(title=title)


def _notice_to_html(the_notice, ctx):
    with H.div(_class=u'notice %s' % the_notice.severity):
        with H.h3():
            # See above regarding spaces.
            H.abbr(the_notice.severity_short, _class=u'severity',
                   title=the_notice.severity)
            H.span(six.text_type(the_notice.ident), _class=u'ident')
            with H.span():
                _piece_to_html(the_notice.title, ctx)
        for piece in the_notice.explanation:
            _piece_to_html(piece, ctx)


def _piece_to_html(piece, ctx):
    if isinstance(piece, list):
        for p in piece:
            _piece_to_html(p, ctx)

    elif isinstance(piece, notice.Paragraph):
        with H.p():
            _piece_to_html(piece.content, ctx)

    elif isinstance(piece, notice.Var):
        target = resolve_reference(ctx, piece.reference)
        with H.span(__inline=True, **_referring_to(target)):
            _piece_to_html(target, ctx)

    elif isinstance(piece, notice.Ref):
        target = resolve_reference(ctx, piece.reference)
        H.span(u'', **_referring_to(target))

    elif isinstance(piece, notice.Cite):
        _piece_to_html(piece.info, ctx)
        quote = piece.content
        if quote:
            H.span(u': ', __inline=True)
            with H.q(__inline=True):
                _piece_to_html(quote, ctx)

    elif isinstance(piece, notice.ExceptionDetails):
        for para in expand_error(ctx['error']):
            with H.p():
                _piece_to_html(para, ctx)

    elif isinstance(piece, Citation):
        with H.cite(__inline=True):
            H.a(piece.title, href=piece.url, target=u'_blank', __inline=True)

    elif isinstance(piece, notice.Known):
        magic = _magic_references(piece, ctx)
        with H.span(__inline=True, **_referring_to(magic)):
            _piece_to_html(piece.content, ctx)

    elif known.is_known(piece):
        _known_to_html(piece)

    elif isinstance(piece, Placeholder):
        H.var(piece.name, __inline=True)

    elif isinstance(piece, six.text_type):
        H.span(printable(piece), __inline=True)

    else:
        _piece_to_html(expand_piece(piece), ctx)


def _displayable_body(msg):
    removing_te = [u'removing Transfer-Encoding'] \
        if msg.headers.transfer_encoding else []
    removing_ce = [u'removing Content-Encoding'] \
        if msg.headers.content_encoding else []
    decoding_charset = [u'decoding from %s' % msg.guessed_charset] \
        if msg.guessed_charset and msg.guessed_charset != 'utf-8' else []
    pretty_printing = [u'pretty-printing']

    if okay(msg.json_data):
        r = json.dumps(msg.json_data, indent=2, ensure_ascii=False)
        transforms = \
            removing_te + removing_ce + decoding_charset + pretty_printing
    elif okay(msg.unicode_body):
        r = msg.unicode_body
        transforms = removing_te + removing_ce + decoding_charset
    elif okay(msg.decoded_body):
        r = msg.decoded_body.decode('utf-8', 'replace')
        transforms = removing_te + removing_ce
    elif okay(msg.body):
        r = msg.body.decode('utf-8', 'replace')
        transforms = removing_te
    else:
        return msg.body, []

    limit = 1000
    if len(r) > limit:
        r = r[:limit]
        transforms += [u'taking the first %d characters' % limit]

    pr = printable(r)
    if r != pr:
        r = pr
        transforms += [u'replacing non-printable characters '
                       u'with the \ufffd sign']

    return r, transforms
