# -*- coding: utf-8; -*-

import re

import dominate
import dominate.tags as H

from httpolice import common, header_view, known, notice
from httpolice.common import Unparseable


def for_object(obj):
    if obj in [None, Unparseable]:
        return {}
    else:
        return {'class': type(obj).__name__, 'id': unicode(id(obj))}


def reference_targets(obj):
    if isinstance(obj, header_view.HeaderView):
        return [u'#' + unicode(id(entry)) for entry in obj.entries]
    elif isinstance(obj, list):
        # Support no. 1013, where we want to highlight all entries,
        # not just the one which is ultimately selected by `SingleHeaderView`.
        # Makes sense in general, so I'm inclined not to consider it a hack.
        return [ref for item in obj for ref in reference_targets(item)]
    else:
        return [u'#' + unicode(id(obj))]


def notice_to_text(the_notice, ctx):
    info = u'%d %s' % (the_notice.ident, the_notice.severity)
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
    elif isinstance(piece, common.Parametrized):
        return piece_to_text(piece.item, ctx)
    elif hasattr(piece, 'name'):
        return piece_to_text(piece.name, ctx)
    else:
        return unicode(piece)


def notice_to_html(the_notice, ctx):
    with H.div(_class='notice notice-%s' % the_notice.tag):
        with H.p(_class='notice-heading', __inline=True):
            with H.span(_class='notice-info'):
                H.span(unicode(the_notice.ident), _class='notice-ident')
                H.span(u' ')
                H.span(the_notice.severity, _class='notice-severity',
                       title=the_notice.tag)
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
            H.a(piece.info.title, href=piece.info.url, target='_blank')
        if piece.contents:
            H.span(u': ')
            with H.q(cite=piece.info.url):
                pieces_to_html(piece.contents, ctx)
    elif hasattr(piece, 'contents'):
        pieces_to_html(piece.contents, ctx)
    elif isinstance(piece, common.Parametrized):
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
    if cite:
        H.a(unicode(obj), _class=cls,
            href=cite.url, title=cite.title, target='_blank')
    else:
        H.span(unicode(obj), _class=cls)


class TextReport(object):

    def __init__(self, outfile):
        self.outfile = outfile
        self.written = False

    def write(self, s):
        self.written = True
        self.outfile.write(s.encode('utf-8'))

    def write_more(self, s):
        if self.written:
            self.write(u'\n')
        self.write(s)

    def render_unparseable(self, node):
        if node is Unparseable:
            self.write_more('\n-- (unparseable)\n')
            return True
        else:
            return False

    def render_notices(self, node):
        for notice_id, context in node.complaints or []:
            the_notice = notice.notices[notice_id]
            self.write_more(notice_to_text(the_notice, context))

    def render_request_line(self, req):
        self.write_more(u'>> %s %s %s\n' %
                        (req.method, req.target, req.version))

    def render_status_line(self, resp):
        self.write_more(u'<< %s %d %s\n' % (
            resp.version, resp.status,
            resp.reason.decode('utf-8', 'replace')))

    def render_message(self, msg):
        for entry in msg.header_entries:
            self.write(u'++ %s: %s\n' %
                       (entry.name, entry.value.decode('ascii', 'ignore')))
        if msg.body is Unparseable:
            self.write(u'\n++ (body is unparseable)\n')
        elif msg.body:
            self.write(u'\n++ (%d bytes of payload body not shown)\n' %
                       len(msg.body))
        for entry in msg.trailer_entries or []:
            self.write(u'++ %s: %s\n' %
                       (entry.name, entry.value.decode('ascii', 'ignore')))

        for entry in msg.header_entries:
            self.render_notices(entry)
        for entry in msg.trailer_entries or []:
            self.render_notices(entry)
        self.render_notices(msg)

    def render_connection(self, connection):
        for exch in connection.exchanges:
            self.write_more(u'================================\n')
            self.render_notices(exch)
            if exch.request:
                if not self.render_unparseable(exch.request):
                    self.render_request_line(exch.request)
                    self.render_message(exch.request)
            for resp in exch.responses or []:
                if not self.render_unparseable(resp):
                    self.render_status_line(resp)
                    self.render_message(resp)

        if connection.unparsed_inbound:
            self.write_more(
                u'++ %d unparsed bytes remaining on the request stream\n' %
                len(connection.unparsed_inbound))
        if connection.unparsed_outbound:
            self.write(
                u'++ %d unparsed bytes remaining on the response stream\n' %
                len(connection.unparsed_outbound))


class HTMLReport(object):

    def __init__(self, outfile):
        self.outfile = outfile
        self.document = dominate.document(title=u'HTTPolice report')
        with self.document.head:
            H.meta(http_equiv='Content-Type',
                   content='text/html; charset=utf-8')
            H.link(rel='stylesheet', href='report.css', type='text/css')
            H.script(src='https://code.jquery.com/jquery-1.11.3.js',
                     type='text/javascript')
            H.script(src='report.js', type='text/javascript')

    def dump(self):
        self.outfile.write(self.document.render().encode('utf-8'))

    def render_notices(self, node):
        if node.complaints:
            with H.div(_class='notices'):
                for notice_ident, context in node.complaints:
                    n = notice.notices[notice_ident]
                    notice_to_html(n, context)

    def render_annotated(self, pieces):
        for piece in pieces:
            with H.span(_class='annotated-piece', **for_object(piece)):
                if isinstance(piece, str):
                    H.span(piece.decode('ascii', 'ignore'))
                else:
                    render_known(piece)

    def render_header_entries(self, entries):
        for entry in entries:
            with H.div(__inline=True, **for_object(entry)):
                with H.span(**for_object(entry.name)):
                    render_known(entry.name)
                H.span(u': ')
                with H.span(**for_object(entry.value)):
                    if entry.annotated:
                        self.render_annotated(entry.annotated)
                    else:
                        H.span(entry.value.decode('ascii', 'ignore'))

    def render_message(self, msg):
        self.render_header_entries(msg.header_entries)

        if msg.body is Unparseable:
            H.p(u'payload body is unparseable', _class='hint')
        elif msg.body:
            H.p(u'%d bytes of payload body not shown' % len(msg.body),
                _class='hint')

        if msg.trailer_entries:
            H.p(u'header fields from the chunked trailer:', _class='hint')
            self.render_header_entries(msg.trailer_entries)

    def render_message_notices(self, msg):
        for entry in msg.header_entries:
            self.render_notices(entry)
        for entry in msg.trailer_entries or []:
            self.render_notices(entry)
        self.render_notices(msg)

    def render_request(self, req):
        if not req:
            return
        if req is Unparseable:
            H.p(u'unparseable request', _class='hint')
            return
        with H.div(**for_object(req)):
            with H.div(_class='review'):
                H.h2(u'Request')
                with H.div(_class='request-line', __inline=True):
                    with H.span(**for_object(req.method)):
                        render_known(req.method)
                    H.span(u' ')
                    H.span(req.target, _class='request-target',
                           **for_object(req.target))
                    H.span(u' ')
                    H.span(req.version, **for_object(req.version))
                self.render_message(req)
            self.render_message_notices(req)
            H.br(_class='clear')

    def render_response(self, resp):
        if not resp:
            return
        if resp is Unparseable:
            H.p(u'unparseable response', _class='hint')
            return
        with H.div(**for_object(resp)):
            with H.div(_class='review'):
                H.h2(u'Response')
                with H.div(_class='status-line', __inline=True):
                    H.span(resp.version, **for_object(resp.version))
                    H.span(u' ')
                    with H.span(**for_object(resp.status)):
                        render_known(resp.status)
                        H.span(u' ')
                        H.span(resp.reason.decode('utf-8', 'ignore'),
                               **for_object(resp.reason))
                self.render_message(resp)
            self.render_message_notices(resp)
            H.br(_class='clear')

    def render_connection(self, conn):
        with self.document:
            for exch in conn.exchanges:
                with H.div(**for_object(exch)):
                    self.render_notices(exch)
                    if exch.request:
                        self.render_request(exch.request)
                    for resp in exch.responses or []:
                        self.render_response(resp)

            if conn.unparsed_inbound:
                H.p('%d unparsed bytes remaining on the request stream' %
                    len(conn.unparsed_inbound),
                    _class=u'unparsed request')
            if conn.unparsed_outbound:
                H.p('%d unparsed bytes remaining on the response stream' %
                    len(conn.unparsed_outbound),
                    _class=u'unparsed outbound')

        self.dump()
