# -*- coding: utf-8; -*-

import pkgutil

import dominate
import dominate.tags as H
from dominate.util import text as text_node
from singledispatch import singledispatch
import six

from httpolice import known, message, notice, structure
from httpolice.__metadata__ import version
from httpolice.citation import Citation
from httpolice.header import HeaderView
from httpolice.reports.common import (expand_error, expand_piece,
                                      find_reason_phrase, resolve_reference)
from httpolice.structure import Unavailable
from httpolice.util.text import nicely_join, printable


###############################################################################
# High-level templates.


css_code = pkgutil.get_data('httpolice.reports', 'html.css').decode('utf-8')
js_code = pkgutil.get_data('httpolice.reports', 'html.js').decode('utf-8')


def html_report(exchanges, buf):
    """Generate an HTML report with check results.

    :param exchanges:
        An iterable of :class:`~httpolice.Exchange` objects.
        They must be already processed by :func:`~httpolice.check_exchange`.

    :param buf:
        The file (or file-like object) to which the report will be written.
        It must be opened in binary mode (not text).

    """
    trashcan = H.div()
    title = u'HTTPolice report'
    document = dominate.document(title=title)
    _common_meta(document)
    with document.head:
        H.script(type=u'text/javascript').add_raw_string(js_code)
    with document.body:
        H.attr(_class=u'report')
    with document:
        H.h1(title)
        _render_exchanges(exchanges, trashcan)
    buf.write(document.render().encode('utf-8'))


class Placeholder(object):

    """A magical placeholder used for rendering the notices list."""

    def __init__(self, name=None):
        self.__name = name

    def get(self, name, _=None):
        return Placeholder(name)

    def __getitem__(self, name):
        return self.get(name)

    def __getattr__(self, name):
        return self.get(name)

    def __str__(self):
        return self.__name


def list_notices(buf):
    """Render the list of all notices to the file-like `buf`."""
    title = u'HTTPolice notices'
    document = dominate.document(title=title)
    _common_meta(document)
    with document.body:
        H.attr(_class=u'notices-list')
    with document:
        H.h1(title)
        placeholder = Placeholder()
        for id_ in sorted(notice.all_notices.keys()):
            _notice_to_html(notice.all_notices[id_], placeholder,
                            with_anchor=True)
    buf.write(document.render().encode('utf-8'))


def _common_meta(document):
    with document:
        H.attr(lang=u'en')
    with document.head:
        H.meta(charset=u'utf-8')
        H.meta(name=u'generator', content=u'HTTPolice %s' % version)
        H.style(type=u'text/css').add_raw_string(css_code)
        H.base(_target=u'blank')


def _render_exchanges(exchanges, trashcan):
    # The ``hr`` elements really help readability in w3m.
    H.hr()
    for exch in exchanges:
        div = H.div(_class=u'exchange')
        with div:
            if exch.request:
                _render_request(exch.request)
                H.hr()
            for resp in exch.responses:
                _render_response(resp)
                H.hr()
            if exch.complaints:
                _render_complaints(exch)
                H.hr()

        # Some exchanges are "complaint boxes", carrying only a complaint.
        # If the user silences that complaint, we end up with an empty box.
        # To avoid adding it to our document, we preemptively add it
        # to a dummy "trash can" element, per Dominate docs:
        #
        #   When the context is closed, any nodes that were not already
        #   added to something get added to the current context.
        #
        if len(div) == 0:
            trashcan.add(div)


def _render_request(req):
    with H.section():
        with H.div(_class=u'message-display'):
            if req.remark:
                H.p(printable(req.remark), _class=u'message-remark')
            with H.h2(), H.code():      # Request line
                # We don't insert spaces here because,
                # without ``__pretty=False``,
                # Dominate renders each element on its own line,
                # thus implicitly creating whitespace.
                with H.span(__pretty=False, **_for_object(req.method)):
                    _render_known(req.method)
                H.span(printable(req.target), **_for_object(req.target))
                if req.version:
                    H.span(printable(req.version), **_for_object(req.version))
            _render_message(req)        # Headers, body and all that
        _render_complaints(req)


def _render_response(resp):
    with H.section():
        with H.div(_class=u'message-display'):
            if resp.remark:
                H.p(printable(resp.remark), _class=u'message-remark')
            with H.h2(), H.code():      # Status line
                # See above regarding spaces.
                if resp.version:
                    H.span(printable(resp.version),
                           **_for_object(resp.version))
                with H.span(**_for_object(resp.status)):
                    _render_known(resp.status)
                    text_node(u' ' + printable(find_reason_phrase(resp)))
            _render_message(resp)       # Headers, body and all that
        _render_complaints(resp)


def _render_message(msg):
    _render_header_entries(msg.annotated_header_entries)

    body, transforms = msg.displayable_body
    if body != u'':
        with H.div(**_for_object(msg.displayable_body, u'body-display')):
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
            # Dominate defaults to ``__pretty=False`` for ``pre``.
            _render_known(entry.name)
            text_node(u': ')
            _render_annotated(annotated)


def _render_annotated(pieces):
    """Render an annotated string as produced by :mod:`httpolice.parse`."""
    for piece in pieces:
        if isinstance(piece, bytes):
            text_node(printable(piece.decode('iso-8859-1')))
        else:
            _render_known(piece)


def _render_complaints(obj):
    if obj.complaints:
        with H.div(_class=u'complaints'):
            for complaint in obj.complaints:
                _notice_to_html(complaint.notice, complaint.context)


###############################################################################
# Support for references (mouseover highlights).

# These references directly correspond to Python object references.
# However, we do not include the raw ``id()`` of objects in the report files,
# but instead "anonymize" them.
# See http://security.stackexchange.com/q/121238/108469

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
    """Find "magical" references from an element in a notice.
    
    See the comment in ``httpolice/notices.xml``.
    """
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


###############################################################################
# Templates for pieces of notice explanations.


def _render_known(obj):
    """Render an instance of one of the :data:`httpolice.known.classes`."""
    text = printable(six.text_type(obj))
    cite = known.citation(obj)
    if cite:
        with H.a(text, href=cite.url, title=None):
            title = known.title(obj, with_citation=True)
            if title:
                H.attr(title=title)
    else:
        return text_node(text)


def _notice_to_html(the_notice, ctx, with_anchor=False):
    anchor = {'id': six.text_type(the_notice.id)} if with_anchor else {}
    with H.div(_class=u'notice %s' % the_notice.severity.name, **anchor):
        with H.h3():
            # See above regarding spaces.
            H.abbr(the_notice.severity_short, _class=u'severity',
                   title=the_notice.severity.name)
            H.span(six.text_type(the_notice.id), _class=u'ident')
            with H.span(__pretty=False):
                _piece_to_html(the_notice.title, ctx)
        for piece in the_notice.explanation:
            _piece_to_html(piece, ctx)


@singledispatch
def _piece_to_html(piece, ctx):
    _piece_to_html(expand_piece(piece), ctx)

@_piece_to_html.register(six.text_type)
def _text_to_html(text, _):
    text_node(printable(text))

@_piece_to_html.register(list)
def _list_to_html(xs, ctx):
    for x in xs:
        _piece_to_html(x, ctx)

@_piece_to_html.register(notice.Paragraph)
def _paragraph_to_html(para, ctx):
    with H.p(__pretty=False):
        _piece_to_html(para.content, ctx)

@_piece_to_html.register(notice.Known)
def _known_elem_to_html(elem, ctx):
    magic = _magic_references(elem, ctx)
    with H.span(**_referring_to(magic)):
        _piece_to_html(elem.content, ctx)

@_piece_to_html.register(notice.Var)
def _var_to_html(var, ctx):
    target = resolve_reference(ctx, var.reference)
    with H.span(**_referring_to(target)):
        _piece_to_html(target, ctx)

@_piece_to_html.register(notice.ExceptionDetails)
def _exc_to_html(_, ctx):
    for para in expand_error(ctx['error']):
        with H.p(__pretty=False):
            _piece_to_html(para, ctx)

@_piece_to_html.register(notice.Cite)
def _cite_elem_to_html(elem, ctx):
    _piece_to_html(elem.info, ctx)
    quote = elem.content
    if quote:
        text_node(u': ')
        with H.q():
            _piece_to_html(quote, ctx)

@_piece_to_html.register(Citation)
def _cite_to_html(cite, _):
    with H.cite():
        H.a(cite.title, href=cite.url)

@_piece_to_html.register(notice.Ref)
def _ref_to_html(ref, ctx):
    target = resolve_reference(ctx, ref.reference)
    H.span(u'', **_referring_to(target))

@_piece_to_html.register(Placeholder)
def _placeholder_to_html(placeholder, _):
    H.var(str(placeholder))

for _cls in known.classes:
    _piece_to_html.register(_cls, lambda obj, _: _render_known(obj))
