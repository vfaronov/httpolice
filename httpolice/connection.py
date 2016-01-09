# -*- coding: utf-8; -*-

from httpolice import common, message, parse, request, response, syntax
from httpolice.common import Unparseable, okay
from httpolice.known import m, st, tc


class Exchange(common.ReportNode):

    self_name = 'exch'

    def __repr__(self):
        return 'Exchange(%r, %r)' % (self.request, self.responses)

    def __init__(self, request_, responses):
        super(Exchange, self).__init__()
        self.request = request_
        self.responses = responses
        for resp in self.responses or []:
            resp.request = self.request


class Connection(common.ReportNode):

    self_name = 'conn'

    def __init__(self, exchanges=None, was_tls=None,
                 unparsed_inbound=None, unparsed_outbound=None):
        super(Connection, self).__init__()
        self.exchanges = exchanges or []
        self.was_tls = was_tls
        self.unparsed_inbound = unparsed_inbound
        self.unparsed_outbound = unparsed_outbound


def check_connection(conn):
    for exch in conn.exchanges:
        if okay(exch):
            check_exchange(exch)


def check_exchange(exch):
    if okay(exch.request):
        request.check_request(exch.request)
    if exch.responses is not None:
        response.check_responses(exch.responses)


def parse_two_streams(inbound, outbound, was_tls=None):
    conn = Connection(was_tls=was_tls)
    parse_requests(conn, inbound)
    parse_responses(conn, outbound)
    return conn


def parse_inbound_stream(stream, was_tls=None):
    conn = Connection(was_tls=was_tls)
    parse_requests(conn, stream)
    return conn


def parse_outbound_stream(stream, was_tls=None):
    conn = Connection(was_tls=was_tls)
    parse_responses(conn, stream)
    return conn


def parse_requests(connection, stream):
    state = parse.State(stream)
    exchanges = []
    while state.sane and not state.is_eof():
        req = _parse_request_heading(state)
        exch = Exchange(req, None)
        exchanges.append(exch)
        state.dump_complaints(exch, u'request heading')
        if req is Unparseable:
            break
        _parse_request_body(req, state)
        req.raw = state.cut()
        state.dump_complaints(req, u'request body framing')
        if not state.sane:
            req.complain(1007)
            break
    connection.exchanges.extend(exchanges)
    connection.unparsed_inbound = state.remaining()


def _parse_request_heading(state):
    try:
        (method_, target, version_) = syntax.request_line.parse(state)
        entries = \
            parse.many(syntax.header_field + ~syntax.crlf).parse(state)
        syntax.crlf.parse(state)
    except parse.ParseError, e:
        state.complain(1006, error=e)
        state.sane = False
        return Unparseable
    else:
        req = request.Request(method_, target, version_, entries)
        return req


def _parse_request_body(req, state):
    # RFC 7230 section 3.3.3.

    if req.headers.transfer_encoding:
        codings = list(req.headers.transfer_encoding)
        if codings.pop() == tc.chunked:
            message.parse_chunked(req, state)
        else:
            req.body = Unparseable
            req.complain(1001)
            state.sane = False
        while codings and (req.body is not Unparseable):
            message.decode_transfer_coding(req, codings.pop())

    elif req.headers.content_length:
        n = req.headers.content_length.value
        if n is Unparseable:
            req.body = Unparseable
            state.sane = False
        else:
            try:
                req.body = parse.nbytes(n, n).parse(state)
            except parse.ParseError:
                req.body = Unparseable
                req.complain(1004)
                state.sane = False

    else:
        req.body = None


def parse_responses(connection, stream):
    # If there are existing exchanges on this connection,
    # it's probably the result of parsing the inbound stream,
    # so these are just requests and we'll need to fill in the responses.
    exchanges = list(connection.exchanges)

    # Skip the exchanges where responses are already filled in.
    while exchanges and exchanges[0].responses:
        exchanges.pop(0)

    # We may also need to add new exchanges, though.
    # This happens either if there were more responses than requests
    # (in which case it's an "internal" problem we need to report),
    # or if there were no requests at all
    # (in which case we're just working with responses and it's OK).
    not_pristine = bool(exchanges)
    new_exchanges = []

    state = parse.State(stream)
    while state.sane and not state.is_eof():
        # Select the next exchange.
        if exchanges:
            exch = exchanges.pop(0)
            exch.responses = []
        else:
            exch = Exchange(None, [])
            new_exchanges.append(exch)
            if not_pristine:
                exch.complain(1008)

        # Parse all responses corresponding to this request.
        # RFC 7230 section 3.3.
        while state.sane:
            resp = _parse_response_heading(state)
            state.dump_complaints(exch, u'response heading')
            exch.responses.append(resp)
            if resp is Unparseable:
                break
            resp.request = exch.request
            _parse_response_body(resp, state, exch.request)
            state.dump_complaints(resp, u'response body framing')
            resp.raw = state.cut()
            if not state.sane: 
                break
            if not resp.status.informational:
                # This is the final response for this request.
                # Proceed to the next.
                break

    connection.exchanges.extend(new_exchanges)
    connection.unparsed_outbound = state.remaining()


def _parse_response_heading(state):
    try:
        (version, status, reason) = syntax.status_line.parse(state)
        entries = parse.many(syntax.header_field + ~syntax.crlf).parse(state)
        syntax.crlf.parse(state)
    except parse.ParseError, e:
        state.complain(1009, error=e)
        state.sane = False
        return Unparseable
    else:
        resp = response.Response(version, status, entries, reason=reason)
        return resp


def _parse_response_body(resp, state, req):
    # RFC 7230 section 3.3.3.
    if resp.status == st.switching_protocols:
        resp.body = None
        resp.complain(1011)
        state.sane = False

    elif okay(req) and req.method == m.CONNECT and resp.status.successful:
        resp.body = None
        resp.complain(1012)
        state.sane = False

    elif (resp.status.informational or
              resp.status in [st.no_content, st.not_modified] or
              (okay(req) and req.method == m.HEAD)):
        resp.body = None

    elif resp.headers.transfer_encoding:
        codings = list(resp.headers.transfer_encoding)
        if codings[-1] == tc.chunked:
            codings.pop()
            message.parse_chunked(resp, state)
        else:
            resp.body = parse.anything.parse(state)
        while codings and (resp.body is not Unparseable):
            message.decode_transfer_coding(resp, codings.pop())
        if not state.sane:
            resp.complain(1010)

    elif resp.headers.content_length.is_present:
        n = resp.headers.content_length.value
        if n is Unparseable:
            resp.body = Unparseable
            state.sane = False
        else:
            try:
                resp.body = parse.nbytes(n, n).parse(state)
            except parse.ParseError:
                resp.body = Unparseable
                resp.complain(1004)
                state.sane = False
        if not state.sane:
            resp.complain(1010)

    else:
        resp.body = parse.anything.parse(state)
