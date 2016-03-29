# -*- coding: utf-8; -*-

from httpolice import message, parse, request, response, structure
from httpolice.blackboard import Blackboard
from httpolice.known import m, st, tc
from httpolice.request import RequestView
from httpolice.response import ResponseView
from httpolice.structure import Unparseable
from httpolice.syntax import rfc7230
from httpolice.syntax.common import CRLF


_header_entries = (
    parse.many(rfc7230.header_field * parse.skip(CRLF(lax=True))) *
    parse.skip(CRLF(lax=True))
)


def analyze_streams(inbound, outbound, scheme=None):
    """
    :type inbound: str
    :type outbound: str
    :type scheme: str | None
    """
    conn = Connection()
    parse_streams(conn, inbound, outbound, scheme=scheme)
    check_connection(conn)
    return conn


def analyze_exchange(request, responses):
    """
    :type request: structure.Request
    :type responses: list[structure.Response]
    """
    req_view = RequestView(request)
    resp_views = [ResponseView(req_view, resp) for resp in responses]
    exch = Exchange(req_view, resp_views)
    check_exchange(exch)
    return exch


class Connection(Blackboard):

    self_name = 'conn'

    def __init__(self, exchanges=None,
                 unparsed_inbound=None, unparsed_outbound=None):
        """
        :type exchanges: list[Exchange]
        :type unparsed_inbound: str | None
        :type unparsed_outbound: str | None
        """
        super(Connection, self).__init__()
        self.exchanges = exchanges or []
        self.unparsed_inbound = unparsed_inbound
        self.unparsed_outbound = unparsed_outbound

    @property
    def sub_nodes(self):
        return self.exchanges


class Exchange(Blackboard):

    self_name = 'exch'

    def __repr__(self):
        return 'Exchange(%r, %r)' % (self.request, self.responses)

    def __init__(self, req, resps):
        """
        :type req: RequestView
        :type resp: list[ResponseView]
        """
        super(Exchange, self).__init__()
        assert all(resp.request is req for resp in resps)
        self.request = req
        self.responses = resps

    @property
    def sub_nodes(self):
        yield self.request
        for resp in self.responses:
            yield resp


def check_connection(conn):
    for exch in conn.exchanges:
        check_exchange(exch)


def check_exchange(exch):
    request.check_request(exch.request)
    response.check_responses(exch.responses)


def parse_streams(connection, inbound, outbound, scheme=None):
    requests = _parse_requests(connection, inbound, scheme)
    _parse_responses(connection, requests, outbound)


def _parse_requests(connection, stream, scheme=None):
    state = parse.State(stream)
    result = []
    while state.sane and not state.is_eof():
        req = _parse_request_heading(state, scheme)
        if req is Unparseable:
            state.dump_complaints(connection, u'request heading')
        else:
            result.append(req)
            _parse_request_body(req, state)
    if not state.is_eof():
        connection.complain(1007)
    connection.unparsed_inbound = state.remaining()
    return result


def _parse_request_heading(state, scheme=None):
    try:
        ((method_, target, version_), entries) = \
            (rfc7230.request_line * _header_entries).parse(state, partial=True)
    except parse.ParseError, e:
        state.sane = False
        state.complain(1006, error=e)
        return Unparseable
    else:
        req = RequestView(structure.Request(scheme, method_, target, version_,
                                            entries))
        state.dump_complaints(req, u'request heading')
        return req


def _parse_request_body(req, state):
    # RFC 7230 section 3.3.3.

    if req.headers.transfer_encoding:
        codings = list(req.headers.transfer_encoding)
        if codings.pop() == tc.chunked:
            message.parse_chunked(req, state)
        else:
            req.inner.body = Unparseable
            req.complain(1001)
            state.sane = False
        while codings and (req.body is not Unparseable):
            message.decode_transfer_coding(req, codings.pop())

    elif req.headers.content_length:
        n = req.headers.content_length.value
        if n is Unparseable:
            req.inner.body = Unparseable
            state.sane = False
        else:
            try:
                req.inner.body = state.consume(n)
            except parse.ParseError:
                req.inner.body = Unparseable
                req.complain(1004)
                state.sane = False

    else:
        req.inner.body = None


def _parse_responses(connection, requests, stream):
    state = parse.State(stream)
    while requests and state.sane and not state.is_eof():
        req = requests.pop(0)
        # Parse all responses corresponding to this request.
        # RFC 7230 section 3.3.
        responses = []
        while state.sane:
            resp = _parse_response_heading(req, state)
            if resp is Unparseable:
                state.dump_complaints(connection, u'request heading')
            else:
                responses.append(resp)
                _parse_response_body(resp, state)
                if (not resp.status.informational) or \
                        (resp.status == st.switching_protocols):
                    # This is the final response for this request.
                    # Proceed to the next request.
                    connection.exchanges.append(Exchange(req, responses))
                    break
    if not state.is_eof():
        if state.sane:
            connection.complain(1008)
        else:
            connection.complain(1010)
    connection.unparsed_outbound = state.remaining()


def _parse_response_heading(req, state):
    try:
        ((version_, status, reason), entries) = \
            (rfc7230.status_line * _header_entries).parse(state, partial=True)
    except parse.ParseError, e:
        state.complain(1009, error=e)
        state.sane = False
        return Unparseable
    else:
        resp = ResponseView(req, structure.Response(req.inner, version_,
                                                    status, reason, entries))
        state.dump_complaints(resp, u'response heading')
        return resp


def _parse_response_body(resp, state):
    req = resp.request

    # RFC 7230 section 3.3.3.
    if resp.status == st.switching_protocols:
        resp.inner.body = None
        resp.complain(1011)
        state.sane = False

    elif req and req.method == m.CONNECT and resp.status.successful:
        resp.inner.body = None
        resp.complain(1012)
        state.sane = False

    elif (resp.status.informational or
              resp.status in [st.no_content, st.not_modified] or
              (req and req.method == m.HEAD)):
        resp.inner.body = None

    elif resp.headers.transfer_encoding:
        codings = list(resp.headers.transfer_encoding)
        if codings[-1] == tc.chunked:
            codings.pop()
            message.parse_chunked(resp, state)
        else:
            resp.inner.body = state.remaining()
        while codings and (resp.body is not Unparseable):
            message.decode_transfer_coding(resp, codings.pop())

    elif resp.headers.content_length.is_present:
        n = resp.headers.content_length.value
        if n is Unparseable:
            resp.inner.body = Unparseable
            state.sane = False
        else:
            try:
                resp.inner.body = state.consume(n)
            except parse.ParseError:
                resp.inner.body = Unparseable
                resp.complain(1004)
                state.sane = False

    else:
        resp.inner.body = state.remaining()
