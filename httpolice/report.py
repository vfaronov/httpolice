# -*- coding: utf-8; -*-

import codecs
import re

import dominate
import dominate.tags as H

from httpolice import known, message, notice
from httpolice.connection import Connection, Exchange
from httpolice.header import HeaderView
from httpolice.request import RequestView
from httpolice.response import ResponseView
from httpolice.structure import Parametrized, Unparseable, okay
from httpolice.util.text import has_nonprintable, nicely_join, printable


def for_object(obj, extra_class=u''):
    assert okay(obj)
    return {
        'class': u'%s %s' % (type(obj).__name__, extra_class),
        'id': unicode(id(obj)),
    }


def reference_targets(obj):
    if isinstance(obj, HeaderView):
        return [u'#' + unicode(id(entry)) for entry in obj.entries]
    elif isinstance(obj, list):
        # Support no. 1013, where we want to highlight all entries,
        # not just the one which is ultimately selected by `SingleHeaderView`.
        # Makes sense in general, so I'm inclined not to consider it a hack.
        return [ref for item in obj for ref in reference_targets(item)]
    else:
        return [u'#' + unicode(id(obj))]


def notice_to_text(the_notice, ctx):
    info = u'%d %s' % (the_notice.ident, the_notice.severity_short)
    title = pieces_to_text(the_notice.title, ctx).strip()
    explanation = u'\n'.join(pieces_to_text(para, ctx).strip()
                             for para in the_notice.explanation)
    return u'**** %s    %s\n%s\n' % (info, title, explanation)


def pieces_to_text(pieces, ctx):
    return u''.join(piece_to_text(p, ctx) for p in pieces)


def piece_to_text(piece, ctx):
    if isinstance(piece, notice.Ref):
        return pieces_to_text(piece.get_contents(ctx), ctx)
    elif isinstance(piece, notice.Citation):
        quote = pieces_to_text(piece.contents, ctx).strip()
        quote = re.sub(ur'\s+', u' ', quote)
        if quote:
            return u'“%s” (%s)' % (quote, piece.info)
        else:
            return piece_to_text(piece.info, ctx)
    elif hasattr(piece, 'contents'):
        return pieces_to_text(piece.contents, ctx)
    elif isinstance(piece, Parametrized):
        return piece_to_text(piece.item, ctx)
    elif hasattr(piece, 'name'):
        return piece_to_text(piece.name, ctx)
    else:
        return unicode(piece)


def notice_to_html(the_notice, ctx, for_example=False):
    with H.div(_class='notice notice-%s' % the_notice.severity):
        with H.p(_class='notice-heading', __inline=True):
            if not for_example:
                with H.span(_class='notice-info'):
                    H.span(unicode(the_notice.ident), _class='notice-ident')
                    H.span(u' ')
                    H.span(the_notice.severity_short, _class='notice-severity',
                           title=the_notice.severity)
                H.span(u' ')
            with H.span(_class='notice-title'):
                pieces_to_html(the_notice.title, ctx)
        for para in the_notice.explanation:
            with H.p(_class='notice-para', __inline=True):
                pieces_to_html(para, ctx)


def pieces_to_html(pieces, ctx):
    for p in pieces:
        piece_to_html(p, ctx)


def piece_to_html(piece, ctx):
    if isinstance(piece, notice.Ref):
        target = piece.resolve(ctx)
        with H.span(data_ref_to=u', '.join(reference_targets(target))):
            pieces_to_html(piece.get_contents(ctx), ctx)
    elif isinstance(piece, notice.Citation):
        with H.cite():
            H.a(unicode(piece.info), href=piece.info.url, target='_blank')
        if piece.contents:
            H.span(u': ')
            with H.q(cite=piece.info.url):
                pieces_to_html(piece.contents, ctx)
    elif hasattr(piece, 'contents'):
        pieces_to_html(piece.contents, ctx)
    elif isinstance(piece, Parametrized):
        piece_to_html(piece.item, ctx)
    elif hasattr(piece, 'name'):
        piece_to_html(piece.name, ctx)
    elif known.is_known(piece):
        render_known(piece)
    else:
        H.span(unicode(piece))


def render_known(obj):
    cls = u'known known-%s' % type(obj).__name__
    cite = known.citation(obj)
    title = known.title(obj, with_citation=True)
    if cite:
        elem = H.a(unicode(obj), _class=cls, href=cite.url, target='_blank')
    else:
        elem = H.span(unicode(obj), _class=cls)
    if title:
        with elem:
            H.attr(title=title)


def _include_stylesheet():
    H.link(rel='stylesheet', href='report.css', type='text/css')


def _include_scripts():
    H.script(src='https://code.jquery.com/jquery-1.11.3.js',
             type='text/javascript')
    H.script(src='report.js', type='text/javascript')


def render_notice_examples(examples):
    doc = dominate.document(title=u'HTTPolice notice examples')
    with doc.head:
        H.meta(http_equiv='Content-Type', content='text/html; charset=utf-8')
        _include_stylesheet()
    with doc:
        H.h1(u'HTTPolice notice examples')
        with H.table(_class='notice-examples'):
            H.thead(H.tr(H.th(u'ID'), H.th(u'severity'), H.th(u'example')))
            with H.tbody():
                for the_notice, ctx in examples:
                    with H.tr():
                        H.td(unicode(the_notice.ident))
                        H.td(the_notice.severity)
                        with H.td():
                            notice_to_html(the_notice, ctx, for_example=True)
    return doc.render().encode('utf-8')


def displayable_body(msg):
    r = msg.body
    transforms = []
    if not okay(r):
        return r, transforms
    if msg.headers.transfer_encoding:
        transforms.append(u'removing Transfer-Encoding')

    if okay(msg.decoded_body):
        r = msg.decoded_body
        if msg.headers.content_encoding:
            transforms.append(u'removing Content-Encoding')
        charset = message.body_charset(msg) or 'UTF-8'
        try:
            codec = codecs.lookup(charset)
        except LookupError:
            codec = codecs.lookup('utf-8')
        r = r.decode(codec.name, 'replace')
        if codec.name != 'utf-8':
            transforms.append(u'decoding from %s' % charset)
    else:
        r = r.decode('utf-8', 'replace')

    if has_nonprintable(r):
        transforms.append(u'replacing non-printable characters '
                          u'with the \ufffd sign')
        r = printable(r)

    limit = 5000
    if len(r) > limit:
        r = r[:limit]
        transforms.append(u'taking the first %d characters' % limit)

    return r, transforms


class Report(object):

    @classmethod
    def render(cls, items, outfile):
        report = cls(outfile)
        for item in items:
            report._render_item(item)
        report._close()

    def __init__(self, outfile):
        self.outfile = outfile

    def _render_item(self, item):
        if isinstance(item, Connection):
            self._render_connection(item)
        elif isinstance(item, Exchange):
            self._render_exchange(item)
        elif isinstance(item, RequestView):
            self._render_request(item)
        elif isinstance(item, ResponseView):
            self._render_response(item)
        else:
            raise TypeError("don't know how to render a %s object" %
                            type(item).__name__)

    def _render_connection(self, conn):
        raise NotImplementedError()

    def _render_exchange(self, exch):
        raise NotImplementedError()

    def _render_request(self, req):
        raise NotImplementedError()

    def _render_response(self, resp):
        raise NotImplementedError()

    def _close(self):
        pass


class TextReport(Report):

    def __init__(self, outfile):
        super(TextReport, self).__init__(outfile)
        self.written = False

    def _render_item(self, item):
        self._write_more(u'================================\n')
        super(TextReport, self)._render_item(item)

    def _write(self, s):
        self.written = True
        self.outfile.write(s.encode('utf-8'))

    def _write_more(self, s):
        if self.written:
            self._write(u'\n')
        self._write(s)

    def _render_notices(self, node):
        for notice_id, context in node.complaints or []:
            the_notice = notice.notices[notice_id]
            self._write_more(notice_to_text(the_notice, context))

    def _render_request_line(self, req):
        self._write_more(u'>> %s %s %s\n' %
                         (req.method, req.target, req.version))

    def _render_status_line(self, resp):
        self._write_more(u'<< %s %d %s\n' % (
            resp.version, resp.status,
            resp.reason.decode('utf-8', 'replace')))

    def _render_message(self, msg):
        for entry in msg.header_entries:
            self._write(u'++ %s: %s\n' %
                        (entry.name, entry.value.decode('ascii', 'ignore')))
        if msg.body is Unparseable:
            self._write(u'\n++ (body is unparseable)\n')
        elif msg.body:
            self._write(u'\n++ (%d bytes of payload body not shown)\n' %
                       len(msg.body))
        for entry in msg.trailer_entries:
            self._write(u'++ %s: %s\n' %
                        (entry.name, entry.value.decode('ascii', 'ignore')))
        self._render_notices(msg)

    def _render_request(self, req):
        self._render_request_line(req)
        self._render_message(req)

    def _render_response(self, resp):
        self._render_status_line(resp)
        self._render_message(resp)

    def _render_exchange(self, exch):
        self._render_request(exch.request)
        for resp in exch.responses:
            self._render_response(resp)
        self._render_notices(exch)

    def _render_connection(self, conn):
        for exch in conn.exchanges:
            self._render_exchange(exch)
        self._render_notices(conn)
        if conn.unparsed_inbound:
            self._write_more(
                u'++ %d unparsed bytes remaining on the request stream\n' %
                len(conn.unparsed_inbound))
        if conn.unparsed_outbound:
            self._write_more(
                u'++ %d unparsed bytes remaining on the response stream\n' %
                len(conn.unparsed_outbound))


class HTMLReport(Report):

    def __init__(self, outfile):
        super(HTMLReport, self).__init__(outfile)
        self.document = dominate.document(title=u'HTTPolice report')
        with self.document.head:
            H.meta(http_equiv='Content-Type',
                   content='text/html; charset=utf-8')
            _include_stylesheet()
            _include_scripts()

    def _close(self):
        self.outfile.write(self.document.render().encode('utf-8'))

    def _render_item(self, item):
        with self.document:
            self._render_next_item(item)

    def _render_next_item(self, item):
        with H.div(**for_object(item)):
            super(HTMLReport, self)._render_item(item)
            self._render_notices(item)
            H.br(_class='item-separator')

    def _render_notices(self, item):
        if item.complaints:
            with H.div(_class='notices'):
                for notice_ident, context in item.complaints:
                    notice_data = notice.notices[notice_ident]
                    notice_to_html(notice_data, context)

    def _render_annotated(self, pieces):
        for piece in pieces:
            with H.span(_class='annotated-piece', **for_object(piece)):
                if isinstance(piece, str):
                    H.span(printable(piece.decode('utf-8', 'replace')))
                else:
                    render_known(piece)

    def _render_header_entries(self, msg, entries, from_trailer):
        for i, entry in enumerate(entries):
            with H.div(__inline=True, **for_object(entry)):
                with H.span(**for_object(entry.name)):
                    render_known(entry.name)
                H.span(u': ')
                with H.span(**for_object(entry.value)):
                    annotated = msg.annotations.get((from_trailer, i))
                    if annotated is not None:
                        self._render_annotated(annotated)
                    else:
                        H.span(
                            printable(entry.value.decode('utf-8', 'replace')))

    def _render_message(self, msg):
        self._render_header_entries(msg, msg.header_entries, False)

        body, transforms = displayable_body(msg)
        if body is Unparseable:
            with H.div(_class='review-block'):
                H.p(u'Payload body is unavailable.', _class='hint')
        elif body:
            with H.div(**for_object(msg.body, extra_class='review-block')):
                if transforms:
                    H.p(u'Payload body after %s:' % nicely_join(transforms),
                        _class='hint')
                H.div(body, _class='payload-body')

        if msg.trailer_entries:
            with H.div(_class='review-block'):
                H.p(u'Header fields from the chunked trailer:', _class='hint')
                self._render_header_entries(msg, msg.trailer_entries, True)

    def _render_request(self, req):
        with H.div(_class='review'):
            with H.div(_class='request-line', __inline=True):
                with H.span(**for_object(req.method)):
                    render_known(req.method)
                H.span(u' ')
                H.span(req.target, _class='request-target',
                       **for_object(req.target))
                H.span(u' ')
                H.span(req.version, **for_object(req.version))
            self._render_message(req)

    def _render_response(self, resp):
        with H.div(_class='review'):
            with H.div(_class='status-line', __inline=True):
                H.span(resp.version, **for_object(resp.version))
                H.span(u' ')
                with H.span(**for_object(resp.status)):
                    render_known(resp.status)
                    H.span(u' ')
                    H.span(
                        printable(resp.reason.decode('utf-8', 'replace')),
                        **for_object(resp.reason))
            self._render_message(resp)

    def _render_exchange(self, exch):
        self._render_next_item(exch.request)
        for resp in exch.responses:
            self._render_next_item(resp)

    def _render_connection(self, conn):
        for exch in conn.exchanges:
            self._render_next_item(exch)
        with H.div(_class='review'):
            if conn.unparsed_inbound:
                H.p('%d unparsed bytes remaining on the request stream' %
                    len(conn.unparsed_inbound),
                    _class=u'unparsed inbound')
            if conn.unparsed_outbound:
                H.p('%d unparsed bytes remaining on the response stream' %
                    len(conn.unparsed_outbound),
                    _class=u'unparsed outbound')
