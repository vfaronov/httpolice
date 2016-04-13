# -*- coding: utf-8; -*-

import codecs
import json
import re

import dominate
import dominate.tags as H
import six

from httpolice import known, message, notice
from httpolice.citation import Citation
from httpolice.header import HeaderView
from httpolice.parse import ParseError, Symbol
from httpolice.structure import HeaderEntry, Parametrized, Unavailable, okay
from httpolice.util.text import (
    ellipsize,
    format_chars,
    has_nonprintable,
    nicely_join,
    printable,
    write_if_any,
)


###############################################################################
# Base code.

class Report(object):

    @classmethod
    def render(cls, exchanges, outfile):
        report = cls(outfile)
        report.render_exchanges(exchanges)
        report.close()

    def __init__(self, outfile):
        self.outfile = outfile

    def render_exchanges(self, exchanges):
        raise NotImplementedError()

    def close(self):
        pass


def displayable_body(msg):
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


def expand_piece(piece):
    if hasattr(piece, 'content'):
        return piece.content

    elif isinstance(piece, Symbol):
        return [piece.name, u' (', piece.citation, u')']

    elif isinstance(piece, Parametrized):
        return piece.item

    elif isinstance(piece, (HeaderEntry, HeaderView)):
        return piece.name

    else:
        return six.text_type(piece)


def expand_parse_error(error):
    paras = [[u'Parse error at byte offset %d.' % error.point]]
    if error.found == b'':
        paras.append([u'Found end of data.'])
    elif error.found is not None:
        paras.append([u'Found: %s' % format_chars([error.found])])

    for i, (option, as_part_of) in enumerate(error.expected):
        if i == 0:
            paras.append([u'Expected:'])
            para = [option]
        else:
            para = [u'or ', option]
        if as_part_of:
            para.append(u' as part of ')
            for j, parent in enumerate(as_part_of):
                para.extend([u' or ', parent] if j > 0 else [parent])
        paras.append(para)

    return paras


def find_reason_phrase(response):
    return response.reason or known.title(response.status) or u'(unknown)'


###############################################################################
# Plain text reports.

class TextReport(Report):

    def render_exchanges(self, exchanges):
        req_i = resp_i = 1
        f1 = self.outfile
        for exch in exchanges:
            with write_if_any(exchange_marker(exch, req_i), f1) as f2:
                if exch.request:
                    req_i += 1
                    for complaint in exch.request.collect_complaints():
                        write_complaint_line(complaint, f2)
                for resp in exch.responses:
                    with write_if_any(response_marker(resp, resp_i), f2) as f3:
                        resp_i += 1
                        for complaint in resp.collect_complaints():
                            write_complaint_line(complaint, f3)
                for complaint in exch.complaints:
                    write_complaint_line(complaint, f2)


def exchange_marker(exchange, req_i):
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


def response_marker(response, resp_i):
    return ellipsize(u'------------ response %d : %d %s' % (
                        resp_i,
                        response.status,
                        printable(find_reason_phrase(response)))) + u'\n'


def write_complaint_line(complaint, f):
    the_notice = notice.notices[complaint.notice_ident]
    title = piece_to_text(the_notice.title, complaint.context).strip()
    f.write(u'%s %d %s\n' % (the_notice.severity_short, the_notice.ident,
                             title))


def piece_to_text(piece, ctx):
    if isinstance(piece, list):
        return u''.join(piece_to_text(p, ctx) for p in piece)

    elif isinstance(piece, notice.Paragraph):
        return piece_to_text(piece.content, ctx) + u'\n'

    elif isinstance(piece, notice.Ref):
        target = piece.resolve_reference(ctx)
        return piece_to_text(piece.content or target, ctx)

    elif isinstance(piece, notice.Cite):
        quote = piece.content
        if quote:
            quote = re.sub(u'\\s+', u' ', piece_to_text(quote, ctx)).strip()
            return u'“%s” (%s)' % (quote, piece.info)
        else:
            return six.text_type(piece.info)

    elif isinstance(piece, ParseError):
        return u''.join(piece_to_text(para, ctx) + u'\n'
                        for para in expand_parse_error(piece))

    elif isinstance(piece, six.text_type):
        return piece

    else:
        return piece_to_text(expand_piece(piece), ctx)


###############################################################################
# HTML reports.


class HTMLReport(Report):

    def __init__(self, outfile):
        super(HTMLReport, self).__init__(outfile)
        self.document = dominate.document(title=u'HTTPolice report')
        with self.document.head:
            H.meta(http_equiv=u'Content-Type',
                   content=u'text/html; charset=utf-8')
            _include_stylesheet()
            _include_scripts()

    def close(self):
        self.outfile.write(self.document.render())

    def render_exchanges(self, exchanges):
        with self.document.body:
            for exch in exchanges:
                with H.div(**for_object(exch)):
                    if exch.request:
                        self._render_request(exch.request)
                    for resp in exch.responses:
                        self._render_response(resp)
                    self._render_complaints(exch)
                    H.br(_class=u'item-separator')

    def _render_complaints(self, obj):
        if obj.complaints:
            with H.div(_class=u'notices'):
                for complaint in obj.complaints:
                    the_notice = notice.notices[complaint.notice_ident]
                    notice_to_html(the_notice, complaint.context)

    def _render_annotated(self, pieces):
        for piece in pieces:
            with H.span(_class=u'annotated-piece', **for_object(piece)):
                if isinstance(piece, bytes):
                    H.span(printable(piece.decode('iso-8859-1')))
                else:
                    known_to_html(piece)

    def _render_header_entries(self, annotated_entries):
        for entry, annotated in annotated_entries:
            with H.div(__inline=True, **for_object(entry)):
                known_to_html(entry.name)
                H.span(u': ')
                self._render_annotated(annotated)

    def _render_message(self, msg):
        self._render_header_entries(msg.annotated_header_entries)

        body, transforms = displayable_body(msg)
        if body is Unavailable:
            with H.div(_class=u'review-block'):
                H.p(u'Payload body is unavailable.', _class=u'hint')
        elif body:
            with H.div(**for_object(msg.body, extra_class=u'review-block')):
                if transforms:
                    H.p(u'Payload body after %s:' % nicely_join(transforms),
                        _class=u'hint')
                H.div(body, _class=u'payload-body')

        if msg.trailer_entries:
            with H.div(_class=u'review-block'):
                H.p(u'Header fields from the trailer part:', _class=u'hint')
                self._render_header_entries(msg.annotated_trailer_entries)

    def _render_request(self, req):
        with H.div(_class=u'review'):
            with H.div(_class=u'request-line', __inline=True):
                with H.span(**for_object(req.method)):
                    known_to_html(req.method)
                H.span(u' ')
                H.span(printable(req.target),
                       **for_object(req.target, u'request-target'))
                H.span(u' ')
                H.span(printable(req.version), **for_object(req.version))
            self._render_message(req)
        self._render_complaints(req)

    def _render_response(self, resp):
        with H.div(_class=u'review'):
            with H.div(_class=u'status-line', __inline=True):
                H.span(printable(resp.version), **for_object(resp.version))
                H.span(u' ')
                with H.span(**for_object(resp.status)):
                    known_to_html(resp.status)
                    H.span(u' ')
                    H.span(printable(find_reason_phrase(resp)))
            self._render_message(resp)
        self._render_complaints(resp)


def _include_stylesheet():
    H.link(rel=u'stylesheet', href=u'report.css', type=u'text/css')


def _include_scripts():
    H.script(src=u'https://code.jquery.com/jquery-1.11.3.js',
             type=u'text/javascript')
    H.script(src=u'report.js', type=u'text/javascript')


def for_object(obj, extra_class=u''):
    assert okay(obj)
    return {
        u'class': u'%s %s' % (type(obj).__name__, extra_class),
        u'id': six.text_type(id(obj)),
    }


def reference_targets(obj):
    if isinstance(obj, HeaderView):
        return [u'#' + six.text_type(id(entry)) for entry in obj.entries]
    elif isinstance(obj, list):
        # Support no. 1013, where we want to highlight all entries,
        # not just the one which is ultimately selected by `SingleHeaderView`.
        # Makes sense in general, so I'm inclined not to consider it a hack.
        return [ref for item in obj for ref in reference_targets(item)]
    else:
        return [u'#' + six.text_type(id(obj))]


def known_to_html(obj):
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


def notice_to_html(the_notice, ctx, for_example=False):
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
                piece_to_html(the_notice.title, ctx)
        for para in the_notice.explanation:
            piece_to_html(para, ctx)


def piece_to_html(piece, ctx):
    if isinstance(piece, list):
        for p in piece:
            piece_to_html(p, ctx)

    elif isinstance(piece, notice.Paragraph):
        with H.p(_class=u'notice-para', __inline=True):
            piece_to_html(piece.content, ctx)

    elif isinstance(piece, notice.Ref):
        target = piece.resolve_reference(ctx)
        with H.span(data_ref_to=u', '.join(reference_targets(target))):
            piece_to_html(piece.content or target, ctx)

    elif isinstance(piece, notice.Cite):
        piece_to_html(piece.info, ctx)
        quote = piece.content
        if quote:
            H.span(u': ')
            with H.q(cite=piece.info.url):
                piece_to_html(quote, ctx)

    elif isinstance(piece, ParseError):
        for para in expand_parse_error(piece):
            with H.p(_class=u'notice-para', __inline=True):
                piece_to_html(para, ctx)

    elif isinstance(piece, Citation):
        with H.cite():
            H.a(piece.title, href=piece.url, target=u'_blank')

    elif known.is_known(piece):
        known_to_html(piece)

    elif isinstance(piece, six.text_type):
        H.span(piece)

    else:
        piece_to_html(expand_piece(piece), ctx)


def render_notice_examples(examples):
    doc = dominate.document(title=u'HTTPolice notice examples')
    with doc.head:
        H.meta(http_equiv=u'Content-Type', content=u'text/html; charset=utf-8')
        _include_stylesheet()
    with doc:
        H.h1(u'HTTPolice notice examples')
        with H.table(_class=u'notice-examples'):
            H.thead(H.tr(H.th(u'ID'), H.th(u'severity'), H.th(u'example')))
            with H.tbody():
                for the_notice, ctx in examples:
                    with H.tr():
                        H.td(six.text_type(the_notice.ident))
                        H.td(the_notice.severity)
                        with H.td():
                            notice_to_html(the_notice, ctx, for_example=True)
    return doc.render()
