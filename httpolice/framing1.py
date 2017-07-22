# -*- coding: utf-8; -*-

"""Parse HTTP/1.x message framing according to RFC 7230."""

import re

from httpolice.citation import RFC
from httpolice.codings import decode_deflate, decode_gzip
from httpolice.exchange import Exchange, complaint_box
from httpolice.known import m, st, tc
from httpolice.parse import ParseError, Symbol
from httpolice.request import Request
from httpolice.response import Response
from httpolice.structure import (FieldName, HeaderEntry, HTTPVersion, Method,
                                 StatusCode, Unavailable, okay)


# Create empty symbols just for referring to them in parse errors.

HTTP_message = Symbol(u'HTTP-message', RFC(7230, section=u'3'))
request_line = Symbol(u'request-line', RFC(7230, section=u'3.1.1'))
status_line = Symbol(u'status-line', RFC(7230, section=u'3.1.2'))
header_field = Symbol(u'header-field', RFC(7230, section=u'3.2'))
chunked_body = Symbol(u'chunked-body', RFC(7230, section=u'4.1'))
chunk = Symbol(u'chunk', RFC(7230, section=u'4.1'))
chunk_size = Symbol(u'chunk-size', RFC(7230, section=u'4.1'))


HTTP_VERSION = re.compile(u'^HTTP/[0-9]\\.[0-9]$')
STATUS_CODE = re.compile(u'^[0-9]{3}$')


MAX_BODY_SIZE = 1024 * 1024 * 1024


def parse_streams(inbound, outbound, scheme=None):
    """Parse one or two HTTP/1.x streams.

    Note that parsing an outbound stream without an inbound stream
    is unreliable, because response framing depends on the request.

    :param inbound:
        The inbound (request) stream as a :class:`~httpolice.stream.Stream`,
        or `None`.
    :param outbound:
        The outbound (response) stream as a :class:`~httpolice.stream.Stream`,
        or `None`.
    :param scheme:
        The scheme of the request URI, as a Unicode string,
        or `None` if unknown.
    :return:
        An iterable of :class:`Exchange` objects.
        Some of the exchanges may be "empty" (aka "complaint boxes"):
        containing neither request nor responses,
        but only a notice that indicates some general problem with the streams.
    """
    while inbound and inbound.good:
        (req, req_box) = _parse_request(inbound, scheme)
        (resps, resp_box) = ([], None)
        if req:
            if outbound and outbound.good:
                (resps, resp_box) = _parse_responses(outbound, req)
                if resps:
                    if resps[-1].status == st.switching_protocols:
                        inbound.sane = False
                    if req.method == m.CONNECT and resps[-1].status.successful:
                        inbound.sane = False
            yield Exchange(req, resps)
        if req_box:
            yield req_box
        if resp_box:
            yield resp_box

    if inbound and not inbound.eof:
        # Some data remains on the inbound stream, but we can't parse it.
        yield complaint_box(1007, stream=inbound, offset=inbound.tell())

    if outbound and outbound.good:
        if inbound:
            # We had some requests, but we ran out of them.
            # We'll still try to parse the remaining responses on their own.
            yield complaint_box(1008, stream=outbound)
        while outbound.good:
            (resps, resp_box) = _parse_responses(outbound, None)
            if resps:
                yield Exchange(None, resps)
            if resp_box:
                yield resp_box

    if outbound and not outbound.eof:
        # Some data remains on the outbound stream, but we can't parse it.
        yield complaint_box(1010, stream=outbound, offset=outbound.tell())


def _parse_request(stream, scheme=None):
    try:
        req = _parse_request_heading(stream, scheme)
    except ParseError as e:
        return (None, complaint_box(1006, error=e))
    else:
        _parse_request_body(req, stream)
        return (req, None)


def _parse_request_heading(stream, scheme=None):
    beginning = stream.tell()
    with stream.parsing(request_line):
        line = stream.readline()
        pieces = line.split(u' ')
        if len(pieces) != 3 or not HTTP_VERSION.match(pieces[2]):
            raise stream.error(beginning)
    method_ = Method(pieces[0])
    target = pieces[1]
    version_ = HTTPVersion(pieces[2])
    entries = parse_header_fields(stream)
    with stream.parsing(HTTP_message):
        stream.readlineend()
    req = Request(scheme, method_, target, version_, entries, body=None,
                  remark=u'from %s, offset %d' % (stream.name, beginning))
    stream.dump_complaints(req.complain, place=u'request heading')
    return req


def _process_content_length(msg, stream):
    n = msg.headers.content_length.value
    if not okay(n):
        msg.body = Unavailable()
        stream.sane = False
    else:
        if n > MAX_BODY_SIZE:
            msg.body = Unavailable()
            stream.sane = False
            msg.complain(1298, place=msg.headers.content_length, size=n,
                         max_size=MAX_BODY_SIZE)
        else:
            try:
                msg.body = stream.read(n)
            except ParseError as exc:
                msg.body = Unavailable()
                msg.complain(1004, error=exc)


def _parse_request_body(req, stream):
    # RFC 7230 section 3.3.3.

    if req.headers.transfer_encoding:
        codings = req.headers.transfer_encoding.value[:]
        if codings.pop() == tc.chunked:
            _parse_chunked(req, stream)
        else:
            req.body = Unavailable()
            req.complain(1001)
            stream.sane = False
        while codings and okay(req.body):
            _decode_transfer_coding(req, codings.pop())

    elif req.headers.content_length:
        _process_content_length(req, stream)

    else:
        req.body = b''


def _parse_responses(stream, req):
    resps = []
    while stream.good:
        # Parse all responses corresponding to one request.
        # RFC 7230 section 3.3.
        try:
            resp = _parse_response_heading(req, stream)
        except ParseError as e:
            return (resps, complaint_box(1009, error=e))
        else:
            resps.append(resp)
            _parse_response_body(resp, stream)
            if (not resp.status.informational) or \
                    (resp.status == st.switching_protocols):
                # This is the final response for this request.
                break
    return (resps, None)


def _parse_response_heading(req, stream):
    beginning = stream.tell()
    with stream.parsing(status_line):
        line = stream.readline()
        pieces = line.split(u' ', 2)
        if len(pieces) != 3 or \
                not HTTP_VERSION.match(pieces[0]) or \
                not STATUS_CODE.match(pieces[1]):
            raise stream.error(beginning)
    version_ = HTTPVersion(pieces[0])
    status = StatusCode(pieces[1])
    reason = pieces[2]
    entries = parse_header_fields(stream)
    with stream.parsing(HTTP_message):
        stream.readlineend()
    resp = Response(
        version_, status, reason, entries, body=None,
        remark=u'from %s, offset %d' % (stream.name, beginning))
    resp.request = req
    stream.dump_complaints(resp.complain, place=u'response heading')
    return resp


def _parse_response_body(resp, stream):
    req = resp.request

    # RFC 7230 section 3.3.3.
    if resp.status == st.switching_protocols:
        resp.body = b''
        resp.complain(1011)
        stream.sane = False

    elif req and req.method == m.CONNECT and resp.status.successful:
        resp.body = b''
        resp.complain(1012)
        stream.sane = False

    elif (resp.status.informational or
              resp.status in [st.no_content, st.not_modified] or
              (req and req.method == m.HEAD)):
        resp.body = b''

    elif resp.headers.transfer_encoding:
        codings = resp.headers.transfer_encoding.value[:]
        if codings[-1] == tc.chunked:
            codings.pop()
            _parse_chunked(resp, stream)
        else:
            resp.body = stream.read()
        while codings and okay(resp.body):
            _decode_transfer_coding(resp, codings.pop())

    elif resp.headers.content_length.is_present:
        _process_content_length(resp, stream)

    else:
        resp.body = stream.read()


def parse_header_fields(stream):
    """Parse a block of HTTP/1.x header fields.

    :param stream: The :class:`~httpolice.stream.Stream` from which to parse.
    :return: A list of :class:`HeaderEntry`.
    :raises: :class:`ParseError`
    """
    entries = []
    while stream.peek() not in [b'\r', b'\n', b'']:
        with stream.parsing(header_field):
            pos = stream.tell()
            line = stream.readline(decode=False)
            (name, colon, v) = line.partition(b':')
            if not colon:
                raise stream.error(pos)
            vs = [v]
            while stream.peek() in [b' ', b'\t']:
                stream.complain(1016)
                vs.append(b' ' + stream.readline(decode=False).lstrip(b' \t'))
        name = FieldName(name.decode('iso-8859-1'))
        value = b''.join(vs).strip(b' \t')
        entries.append(HeaderEntry(name, value))
    return entries


def _decode_transfer_coding(msg, coding):
    if coding == tc.chunked:
        # The outermost chunked has already been peeled off at this point.
        msg.complain(1002)
        msg.body = Unavailable(msg.body)
    elif coding == tc.gzip or coding == tc.x_gzip:
        try:
            msg.body = decode_gzip(msg.body)
        except Exception as e:
            msg.complain(1027, coding=coding, error=e)
            msg.body = Unavailable(msg.body)
    elif coding == tc.deflate:
        try:
            msg.body = decode_deflate(msg.body)
        except Exception as e:
            msg.complain(1027, coding=coding, error=e)
            msg.body = Unavailable(msg.body)
    else:
        if okay(coding):
            msg.complain(1003, coding=coding)
        msg.body = Unavailable(msg.body)


class BodyTooLongError(Exception):

    def __init__(self, size, max_size):
        super(BodyTooLongError, self).__init__(u'body longer than %d bytes' %
                                               max_size)
        self.size = size
        self.max_size = max_size


def _parse_chunk(stream, data):
    current_size = sum(len(c) for c in data)
    with stream.parsing(chunk):
        pos = stream.tell()
        (size_s, _, _) = stream.readline().partition(u';')
        with stream.parsing(chunk_size):
            try:
                size = int(size_s.rstrip(u' \t'), 16)     # RFC errata ID: 4667
            except ValueError:
                raise stream.error(pos)
        if size == 0:
            return False
        elif size + current_size > MAX_BODY_SIZE:
            stream.sane = False
            raise BodyTooLongError(size + current_size, MAX_BODY_SIZE)
        else:
            data.append(stream.read(size))
            stream.readlineend()
            return True


def _parse_chunked(msg, stream):
    data = []
    place = u'chunked framing'
    try:
        while _parse_chunk(stream, data):
            pass
        trailer = parse_header_fields(stream)
        with stream.parsing(chunked_body):
            stream.readlineend()
    except ParseError as e:
        msg.complain(1005, error=e)
        msg.body = Unavailable()
    except BodyTooLongError as e:
        msg.complain(1298, place=place, size=e.size, max_size=e.max_size)
        msg.body = Unavailable()
    else:
        stream.dump_complaints(msg.complain, place=place)
        msg.body = b''.join(data)
        msg.trailer_entries = trailer
        if trailer:
            msg.rebuild_headers()           # Rebuild the `HeadersView` cache
