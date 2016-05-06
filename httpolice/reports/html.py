# -*- coding: utf-8; -*-

import json

import dominate
import dominate.tags as H
import pkg_resources
from singledispatch import singledispatch
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
    """Generate an HTML report with check results.

    :param exchanges:
        An iterable of :class:`~httpolice.Exchange` objects.
        They must be already processed by :func:`~httpolice.check_exchange`.

    :param buf:
        The file (or file-like object) to which the report will be written.
        It must be opened in binary mode (not text).

    """
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
            for id_ in sorted(notice.notices.keys()):
                _notice_to_html(notice.notices[id_], placeholder,
                                with_anchor=True)
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
                    _render_known(req.method)
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
                    _render_known(resp.status)
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
            _render_known(entry.name)
            H.span(u': ')
            _render_annotated(annotated)


def _render_annotated(pieces):
    for piece in pieces:
        if isinstance(piece, bytes):
            H.span(printable(piece.decode('iso-8859-1')))
        else:
            with H.span(**_for_object(piece)):
                _render_known(piece)


def _render_complaints(obj):
    if obj.complaints:
        with H.div(_class=u'complaints'):
            for complaint in obj.complaints:
                the_notice = notice.notices[complaint.notice_id]
                _notice_to_html(the_notice, complaint.context)


_seen_ids = {}


def _anonymize_id(id_):
    if id_ not in _seen_ids:
        _seen_ids[id_] = len(_seen_ids)
    return _seen_ids[id_]


@singledispatch
def _reference_ids(obj):
    return [six.text_type(_anonymize_id(id(obj)))]

@_reference_ids.register(list)
def _list_reference_ids(xs):
    return [ref for x in xs for ref in _reference_ids(x)]

@_reference_ids.register(HeaderView)
def _header_reference_ids(hdr):
    return _reference_ids(hdr.entries)


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


def _render_known(obj):
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


def _notice_to_html(the_notice, ctx, with_anchor=False):
    anchor = {'id': six.text_type(the_notice.id)} if with_anchor else {}
    with H.div(_class=u'notice %s' % the_notice.severity, **anchor):
        with H.h3():
            # See above regarding spaces.
            H.abbr(the_notice.severity_short, _class=u'severity',
                   title=the_notice.severity)
            H.span(six.text_type(the_notice.id), _class=u'ident')
            with H.span():
                _piece_to_html(the_notice.title, ctx)
        for piece in the_notice.explanation:
            _piece_to_html(piece, ctx)


@singledispatch
def _piece_to_html(piece, ctx):
    _piece_to_html(expand_piece(piece), ctx)

@_piece_to_html.register(six.text_type)
def _text_to_html(text, _):
    H.span(printable(text), __inline=True)

@_piece_to_html.register(list)
def _list_to_html(xs, ctx):
    for x in xs:
        _piece_to_html(x, ctx)

@_piece_to_html.register(notice.Paragraph)
def _paragraph_to_html(para, ctx):
    with H.p():
        _piece_to_html(para.content, ctx)

@_piece_to_html.register(notice.Known)
def _known_elem_to_html(elem, ctx):
    magic = _magic_references(elem, ctx)
    with H.span(__inline=True, **_referring_to(magic)):
        _piece_to_html(elem.content, ctx)

@_piece_to_html.register(notice.Var)
def _var_to_html(var, ctx):
    target = resolve_reference(ctx, var.reference)
    with H.span(__inline=True, **_referring_to(target)):
        _piece_to_html(target, ctx)

@_piece_to_html.register(notice.ExceptionDetails)
def _exc_to_html(_, ctx):
    for para in expand_error(ctx['error']):
        with H.p():
            _piece_to_html(para, ctx)

@_piece_to_html.register(notice.Cite)
def _cite_elem_to_html(elem, ctx):
    _piece_to_html(elem.info, ctx)
    quote = elem.content
    if quote:
        H.span(u': ', __inline=True)
        with H.q(__inline=True):
            _piece_to_html(quote, ctx)

@_piece_to_html.register(Citation)
def _cite_to_html(cite, _):
    with H.cite(__inline=True):
        H.a(cite.title, href=cite.url, target=u'_blank', __inline=True)

@_piece_to_html.register(notice.Ref)
def _ref_to_html(ref, ctx):
    target = resolve_reference(ctx, ref.reference)
    H.span(u'', **_referring_to(target))

@_piece_to_html.register(Placeholder)
def _placeholder_to_html(placeholder, _):
    H.var(placeholder.name, __inline=True)

for _cls in known.classes:
    _piece_to_html.register(_cls, lambda obj, _: _render_known(obj))


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
