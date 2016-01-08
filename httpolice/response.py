# -*- coding: utf-8; -*-

from httpolice import common, message, parse, syntax
from httpolice.common import Unparseable, okay
from httpolice.known import m, st, tc


class Response(message.Message):

    def __repr__(self):
        return '<Response %d>' % self.status

    def __init__(self, request, version, status, header_entries,
                 body=None, trailer_entries=None, raw=None):
        super(Response, self).__init__(version, header_entries,
                                       body, trailer_entries, raw)
        self.request = request
        self.status = status


class Exchange(common.ReportNode):

    self_name = 'exch'

    def __repr__(self):
        return 'Exchange(%r, %r)' % (self.request, self.responses)

    def __init__(self, request, responses):
        super(Exchange, self).__init__()
        self.request = request
        self.responses = responses


class Connection(common.ReportNode):

    self_name = 'conn'

    def __init__(self, exchanges):
        super(Connection, self).__init__()
        self.exchanges = exchanges


def parse_stream(stream, requests=None):
    state = parse.State(stream)
    exchanges = []
    while not state.is_eof():
        # Select the next request.
        if requests is None:
            req = None
        elif requests:
            req = requests[0]
            requests = requests[1:]
        else:
            exchanges.append(Exchange(None, [Unparseable]))
            return exchanges

        exchange = Exchange(req, [])
        exchanges.append(exchange)

        # Parse all responses corresponding to this request.
        # RFC 7230 section 3.3.
        while True:
            resp, stream_ok = _parse_one(state, req)
            exchange.responses.append(resp)
            if not stream_ok:
                return exchanges
            if not resp.status.informational:
                # This is the final response for this request.
                # Proceed to the next.
                break

    return exchanges


def _parse_one(state, req):
    try:
        (version, status) = syntax.status_line.parse(state)
        entries = parse.many(syntax.header_field + ~syntax.crlf).parse(state)
        syntax.crlf.parse(state)
    except parse.ParseError:
        return Unparseable, False
    resp = Response(req, version, status, entries)
    resp.body = Unparseable

    # RFC 7230 section 3.3.3.

    if (resp.status.informational or
            resp.status in [st.no_content, st.not_modified] or
            (okay(req) and req.method == m.HEAD)):
        resp.body = None
        return resp, (resp.status != st.switching_protocols)

    if okay(req) and req.method == m.CONNECT and resp.status.successful:
        resp.body = None
        return resp, False

    if resp.headers.transfer_encoding:
        codings = list(resp.headers.transfer_encoding)
        if codings[-1] == tc.chunked:
            codings.pop()
            if not message.parse_chunked(resp, state):
                return resp, False
        else:
            resp.body = parse.anything.parse(state)
        while codings and (resp.body is not Unparseable):
            message.decode_transfer_coding(resp, codings.pop())
    elif resp.headers.content_length.is_present:
        n = resp.headers.content_length.value
        if n is Unparseable:
            return resp, False
        try:
            resp.body = parse.nbytes(n, n).parse(state)
        except parse.ParseError:
            resp.complain(1004)
            return resp, False
    else:
        resp.body = parse.anything.parse(state)

    return resp, True
