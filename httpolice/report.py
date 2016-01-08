# -*- coding: utf-8; -*-

import re

from httpolice import common, notice
from httpolice.common import Unparseable
from httpolice.known import status_code


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
        reason = status_code.description(resp.status) or u''
        self.write_more(u'<< %s %d %s\n' % (resp.version, resp.status, reason))

    def render_message(self, msg):
        for entry in msg.header_entries:
            self.write(u'++ %s: %s\n' %
                       (entry.name, entry.value.decode('ascii', 'ignore')))
        if msg.body is Unparseable:
            self.write(u'\n++ (body is unparseable)\n')
        elif msg.body:
            self.write(u'\n++ (%d bytes of payload body not shown)\n' %
                       len(msg.body))

        for entry in msg.header_entries:
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
