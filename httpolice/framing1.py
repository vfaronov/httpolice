# -*- coding: utf-8; -*-

from httpolice.codings import decode_deflate, decode_gzip
from httpolice.exchange import ExchangeView, check_exchange, complaint_box
from httpolice.known import m, st, tc
from httpolice.parse import ParseError, Stream, maybe, skip
from httpolice.request import RequestView
from httpolice.response import ResponseView
from httpolice.structure import (
    FieldName,
    HTTPVersion,
    HeaderEntry,
    Method,
    Request,
    Response,
    StatusCode,
    Unavailable,
)
from httpolice.syntax import rfc7230
from httpolice.syntax.common import CRLF, LF, SP


def parse_streams(inbound, outbound, scheme=None):
    """
    :type inbound: bytes | None
    :type outbound: bytes | None
    :type scheme: six.text_type | bytes | None
    """
    inbound = None if inbound is None else Stream(inbound)
    outbound = None if outbound is None else Stream(outbound)
    while inbound and inbound.sane:
        (req, req_box) = _parse_request(inbound, scheme)
        (resps, resp_box) = ([], None)
        if req:
            if outbound and outbound.sane:
                (resps, resp_box) = _parse_responses(outbound, req)
                if resps:
                    if resps[-1].status == st.switching_protocols:
                        inbound.sane = False
                    if req.method == m.CONNECT and resps[-1].status.successful:
                        inbound.sane = False
            yield ExchangeView(req, resps)
        if req_box:
            yield req_box
        if resp_box:
            yield resp_box

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
            _parse_line_ending(stream)
            entries = parse_header_fields(stream)
    except ParseError as e:
        stream.sane = False
        stream.complain(1006, error=e)
        return Unavailable
    else:
        req = RequestView(Request(scheme, method_, target, version_, entries,
                                  body=Unavailable))
        stream.dump_complaints(req, u'request heading')
        return req


def _parse_request_body(req, stream):
    # RFC 7230 section 3.3.3.

    if req.headers.transfer_encoding:
        codings = list(req.headers.transfer_encoding)
        if codings.pop() == tc.chunked:
            _parse_chunked(req, stream)
        else:
            req.inner.body = Unavailable
            req.complain(1001)
            stream.sane = False
        while codings and (req.body is not Unavailable):
            _decode_transfer_coding(req, codings.pop())

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
            _parse_line_ending(stream)
            entries = parse_header_fields(stream)
    except ParseError as e:
        stream.complain(1009, error=e)
        stream.sane = False
        return Unavailable
    else:
        resp = ResponseView(req, Response(version_, status, reason, entries,
                                          body=Unavailable))
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
            _parse_chunked(resp, stream)
        else:
            resp.inner.body = stream.consume_rest()
        while codings and (resp.body is not Unavailable):
            _decode_transfer_coding(resp, codings.pop())

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


def _parse_line_ending(stream):
    r = stream.maybe_consume_regex(CRLF)
    if r is None:
        r = stream.consume_regex(LF, u'line ending')
        stream.complain(1224)
    return r


def parse_header_fields(stream):
    entries = []
    while True:
        name = stream.maybe_consume_regex(rfc7230.field_name)
        if name is None:
            break
        stream.consume_regex(b':')
        stream.consume_regex(rfc7230.OWS)
        vs = []
        while True:
            v = stream.maybe_consume_regex(rfc7230.field_content)
            if v is None:
                if stream.maybe_consume_regex(rfc7230.obs_fold):
                    stream.complain(1016)
                    vs.append(b' ')
                else:
                    break
            else:
                vs.append(v.encode('iso-8859-1'))       # back to bytes
        value = b''.join(vs)
        stream.consume_regex(rfc7230.OWS)
        _parse_line_ending(stream)
        entries.append(HeaderEntry(FieldName(name), value))
    _parse_line_ending(stream)
    return entries


def _decode_transfer_coding(msg, coding):
    if coding == tc.chunked:
        # The outermost chunked has already been peeled off at this point.
        msg.complain(1002)
        msg.inner.body = Unavailable
    elif coding in [tc.gzip, tc.x_gzip]:
        try:
            msg.inner.body = decode_gzip(msg.body)
        except Exception as e:
            msg.complain(1027, coding=coding, error=e)
            msg.inner.body = Unavailable
    elif coding == tc.deflate:
        try:
            msg.inner.body = decode_deflate(msg.body)
        except Exception as e:
            msg.complain(1027, coding=coding, error=e)
            msg.inner.body = Unavailable
    else:
        msg.complain(1003, coding=coding)
        msg.inner.body = Unavailable


def _parse_chunk(stream):
    size = stream.parse(rfc7230.chunk_size * skip(maybe(rfc7230.chunk_ext)))
    _parse_line_ending(stream)
    if size == 0:
        return b''
    else:
        data = stream.consume_n_bytes(size)
        _parse_line_ending(stream)
        return data


def _parse_chunked(msg, stream):
    data = []
    try:
        with stream:
            chunk = _parse_chunk(stream)
            while chunk:
                data.append(chunk)
                chunk = _parse_chunk(stream)
            trailer = parse_header_fields(stream)
    except ParseError as e:
        stream.sane = False
        msg.complain(1005, error=e)
        msg.inner.body = Unavailable
    else:
        stream.dump_complaints(msg, u'chunked framing')
        msg.inner.body = b''.join(data)
        msg.inner.trailer_entries = trailer
        if trailer:
            msg.rebuild_headers()           # Rebuid the `HeadersView` cache
