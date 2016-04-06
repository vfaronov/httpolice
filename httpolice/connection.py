# -*- coding: utf-8; -*-

from httpolice import message, request, response, structure
from httpolice.blackboard import Blackboard
from httpolice.known import m, st, tc
from httpolice.parse import ParseError, Stream
from httpolice.request import RequestView
from httpolice.response import ResponseView
from httpolice.structure import HTTPVersion, Method, StatusCode, Unparseable
from httpolice.syntax import rfc7230
from httpolice.syntax.common import SP


def analyze_streams(inbound, outbound, scheme=None):
    """
    :type inbound: str
    :type outbound: str
    :type scheme: unicode | None
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


def _parse_requests(connection, data, scheme=None):
    stream = Stream(data)
    result = []
    while stream.sane and not stream.is_eof():
        req = _parse_request_heading(stream, scheme)
        if req is Unparseable:
            stream.dump_complaints(connection, u'request heading')
        else:
            result.append(req)
            _parse_request_body(req, stream)
    if not stream.is_eof():
        connection.complain(1007)
    connection.unparsed_inbound = stream.consume_rest()
    return result


def _parse_request_heading(stream, scheme=None):
    try:
        with stream:
            method_ = Method(stream.consume_regex(rfc7230.method))
            stream.consume_regex(SP)
            target = stream.consume_regex('[^ \t]+', 'request target'). \
                decode('iso-8859-1')
            stream.consume_regex(SP)
            version_ = HTTPVersion(stream.consume_regex(rfc7230.HTTP_version))
            message.parse_line_ending(stream)
            entries = message.parse_header_fields(stream)
    except ParseError, e:
        stream.sane = False
        stream.complain(1006, error=e)
        return Unparseable
    else:
        req = RequestView(structure.Request(scheme, method_, target, version_,
                                            entries))
        stream.dump_complaints(req, u'request heading')
        return req


def _parse_request_body(req, stream):
    # RFC 7230 section 3.3.3.

    if req.headers.transfer_encoding:
        codings = list(req.headers.transfer_encoding)
        if codings.pop() == tc.chunked:
            message.parse_chunked(req, stream)
        else:
            req.inner.body = Unparseable
            req.complain(1001)
            stream.sane = False
        while codings and (req.body is not Unparseable):
            message.decode_transfer_coding(req, codings.pop())

    elif req.headers.content_length:
        n = req.headers.content_length.value
        if n is Unparseable:
            req.inner.body = Unparseable
            stream.sane = False
        else:
            try:
                req.inner.body = stream.consume_n_bytes(n)
            except ParseError:
                req.inner.body = Unparseable
                req.complain(1004)
                stream.sane = False

    else:
        req.inner.body = None


def _parse_responses(connection, requests, data):
    stream = Stream(data)
    while requests and stream.sane and not stream.is_eof():
        req = requests.pop(0)
        # Parse all responses corresponding to this request.
        # RFC 7230 section 3.3.
        responses = []
        while stream.sane:
            resp = _parse_response_heading(req, stream)
            if resp is Unparseable:
                stream.dump_complaints(connection, u'request heading')
            else:
                responses.append(resp)
                _parse_response_body(resp, stream)
                if (not resp.status.informational) or \
                        (resp.status == st.switching_protocols):
                    # This is the final response for this request.
                    # Proceed to the next request.
                    connection.exchanges.append(Exchange(req, responses))
                    break
    if not stream.is_eof():
        if stream.sane:
            connection.complain(1008)
        else:
            connection.complain(1010)
    connection.unparsed_outbound = stream.consume_rest()


def _parse_response_heading(req, stream):
    try:
        with stream:
            version_ = HTTPVersion(stream.consume_regex(rfc7230.HTTP_version))
            stream.consume_regex(SP)
            status = StatusCode(stream.consume_regex(rfc7230.status_code))
            stream.consume_regex(SP)
            reason = stream.consume_regex(rfc7230.reason_phrase). \
                decode('iso-8859-1')
            message.parse_line_ending(stream)
            entries = message.parse_header_fields(stream)
    except ParseError, e:
        stream.complain(1009, error=e)
        stream.sane = False
        return Unparseable
    else:
        resp = ResponseView(req, structure.Response(req.inner, version_,
                                                    status, reason, entries))
        stream.dump_complaints(resp, u'response heading')
        return resp


def _parse_response_body(resp, stream):
    req = resp.request

    # RFC 7230 section 3.3.3.
    if resp.status == st.switching_protocols:
        resp.inner.body = None
        resp.complain(1011)
        stream.sane = False

    elif req and req.method == m.CONNECT and resp.status.successful:
        resp.inner.body = None
        resp.complain(1012)
        stream.sane = False

    elif (resp.status.informational or
              resp.status in [st.no_content, st.not_modified] or
              (req and req.method == m.HEAD)):
        resp.inner.body = None

    elif resp.headers.transfer_encoding:
        codings = list(resp.headers.transfer_encoding)
        if codings[-1] == tc.chunked:
            codings.pop()
            message.parse_chunked(resp, stream)
        else:
            resp.inner.body = stream.consume_rest()
        while codings and (resp.body is not Unparseable):
            message.decode_transfer_coding(resp, codings.pop())

    elif resp.headers.content_length.is_present:
        n = resp.headers.content_length.value
        if n is Unparseable:
            resp.inner.body = Unparseable
            stream.sane = False
        else:
            try:
                resp.inner.body = stream.consume_n_bytes(n)
            except ParseError:
                resp.inner.body = Unparseable
                resp.complain(1004)
                stream.sane = False

    else:
        resp.inner.body = stream.consume_rest()
