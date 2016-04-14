# -*- coding: utf-8; -*-

from httpolice import message, request, response, structure
from httpolice.blackboard import Blackboard
from httpolice.known import m, st, tc
from httpolice.parse import ParseError, Stream
from httpolice.request import RequestView
from httpolice.response import ResponseView
from httpolice.structure import HTTPVersion, Method, StatusCode, Unavailable
from httpolice.syntax import rfc7230
from httpolice.syntax.common import SP


def analyze_streams(inbound, outbound, scheme=None):
    """
    :type inbound: bytes | None
    :type outbound: bytes | None
    :type scheme: six.text_type | bytes | None
    """
    inbound = None if inbound is None else Stream(inbound)
    outbound = None if outbound is None else Stream(outbound)
    for exch in parse_streams(inbound, outbound, scheme=scheme):
        check_exchange(exch)
        yield exch


def analyze_exchange(exch):
    """
    :type exch: structure.Exchange
    """
    req_view = RequestView(exch.request) if exch.request else None
    resp_views = [ResponseView(req_view, resp)
                  for resp in exch.responses or []]
    exch = ExchangeView(req_view, resp_views)
    check_exchange(exch)
    return exch


class ExchangeView(Blackboard):

    self_name = u'exch'

    def __repr__(self):
        return 'ExchangeView(%r, %r)' % (self.request, self.responses)

    def __init__(self, req, resps):
        """
        :type req: RequestView
        :type resp: list[ResponseView]
        """
        super(ExchangeView, self).__init__()
        assert all(resp.request is req for resp in resps)
        self.request = req
        self.responses = resps

    @property
    def sub_nodes(self):
        if self.request:
            yield self.request
        for resp in self.responses:
            yield resp


def complaint_box(*args, **kwargs):
    box = ExchangeView(None, [])
    box.complain(*args, **kwargs)
    return box


def check_exchange(exch):
    if exch.request:
        request.check_request(exch.request)
    response.check_responses(exch.responses)


def parse_streams(inbound, outbound, scheme=None):
    """
    :type inbound: Stream | None
    :type outbound: Stream | None
    :type scheme: six.text_type | bytes | None
    """
    while inbound and inbound.sane:
        (req, req_box) = _parse_request(inbound, scheme)
        (resps, resp_box) = ([], None)
        switched = False
        if req:
            if outbound and outbound.sane:
                (resps, resp_box) = _parse_responses(outbound, req)
                if resps:
                    if resps[-1].status == st.switching_protocols:
                        switched = True
                    if req.method == m.CONNECT and resps[-1].status.successful:
                        switched = True
            yield ExchangeView(req, resps)
        if req_box:
            yield req_box
        if resp_box:
            yield resp_box
        if switched:
            break

    if inbound and not inbound.eof:
        yield complaint_box(1007, nbytes=len(inbound.consume_rest()))

    if outbound and outbound.sane:
        if inbound:
            # We had some requests, but we ran out of them.
            # We'll still try to parse the remaining responses on their own.
            yield complaint_box(1008)
        while outbound.sane:
            (resps, resp_box) = _parse_responses(outbound, None)
            if resps:
                yield ExchangeView(None, resps)
            if resp_box:
                yield resp_box

    if outbound and not outbound.eof:
        yield complaint_box(1010, nbytes=len(outbound.consume_rest()))


def _parse_request(stream, scheme=None):
    req = _parse_request_heading(stream, scheme)
    if req is Unavailable:
        box = ExchangeView(None, [])
        stream.dump_complaints(box, u'request heading')
        return (None, box)
    else:
        _parse_request_body(req, stream)
        return (req, None)


def _parse_request_heading(stream, scheme=None):
    try:
        with stream:
            method_ = Method(stream.consume_regex(rfc7230.method))
            stream.consume_regex(SP)
            target = stream.consume_regex(b'[^ \t]+', u'request target')
            stream.consume_regex(SP)
            version_ = HTTPVersion(stream.consume_regex(rfc7230.HTTP_version))
            message.parse_line_ending(stream)
            entries = message.parse_header_fields(stream)
    except ParseError as e:
        stream.sane = False
        stream.complain(1006, error=e)
        return Unavailable
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
            req.inner.body = Unavailable
            req.complain(1001)
            stream.sane = False
        while codings and (req.body is not Unavailable):
            message.decode_transfer_coding(req, codings.pop())

    elif req.headers.content_length:
        n = req.headers.content_length.value
        if n is Unavailable:
            req.inner.body = Unavailable
            stream.sane = False
        else:
            try:
                req.inner.body = stream.consume_n_bytes(n)
            except ParseError:
                req.inner.body = Unavailable
                req.complain(1004)
                stream.sane = False

    else:
        req.inner.body = None


def _parse_responses(stream, req):
    resps = []
    while stream.sane:
        # Parse all responses corresponding to one request.
        # RFC 7230 section 3.3.
        resp = _parse_response_heading(req, stream)
        if resp is Unavailable:
            box = ExchangeView(None, [])
            stream.dump_complaints(box, u'response heading')
            return (resps, box)
        else:
            resps.append(resp)
            _parse_response_body(resp, stream)
            if (not resp.status.informational) or \
                    (resp.status == st.switching_protocols):
                # This is the final response for this request.
                break
    return (resps, None)


def _parse_response_heading(req, stream):
    try:
        with stream:
            version_ = HTTPVersion(stream.consume_regex(rfc7230.HTTP_version))
            stream.consume_regex(SP)
            status = StatusCode(stream.consume_regex(rfc7230.status_code))
            stream.consume_regex(SP)
            reason = stream.consume_regex(rfc7230.reason_phrase)
            message.parse_line_ending(stream)
            entries = message.parse_header_fields(stream)
    except ParseError as e:
        stream.complain(1009, error=e)
        stream.sane = False
        return Unavailable
    else:
        resp = ResponseView(req, structure.Response(version_, status, reason,
                                                    entries))
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
        while codings and (resp.body is not Unavailable):
            message.decode_transfer_coding(resp, codings.pop())

    elif resp.headers.content_length.is_present:
        n = resp.headers.content_length.value
        if n is Unavailable:
            resp.inner.body = Unavailable
            stream.sane = False
        else:
            try:
                resp.inner.body = stream.consume_n_bytes(n)
            except ParseError:
                resp.inner.body = Unavailable
                resp.complain(1004)
                stream.sane = False

    else:
        resp.inner.body = stream.consume_rest()
