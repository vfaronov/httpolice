# -*- coding: utf-8; -*-

from datetime import datetime, timedelta
import email.errors
import gzip
import io
import json
import zlib

try:
    from email import message_from_bytes as parse_email_message
except ImportError:                             # Python 2
    from email import message_from_string as parse_email_message

try:
    from urllib.parse import parse_qs
except ImportError:                             # Python 2
    from urlparse import parse_qs

import defusedxml
import defusedxml.ElementTree
from bitstring import Bits
import six

from httpolice.blackboard import Blackboard, memoized_property
from httpolice.header import HeadersView
from httpolice.known import cc, header, media, media_type, tc, warn
from httpolice.parse import ParseError, maybe, skip
from httpolice.structure import HeaderEntry, FieldName, Unparseable, okay
from httpolice.syntax import rfc7230
from httpolice.syntax.common import CRLF, LF


# This list is taken from the HTML specification --
# http://www.w3.org/TR/html/forms.html#url-encoded-form-data --
# as the exhaustive list of bytes that can be output
# by a "conformant" URL encoder.

URL_ENCODED_GOOD_BYTES = Bits(
    1 if (x in [0x25, 0x26, 0x2A, 0x2B, 0x2D, 0x2E, 0x5F] or
          0x30 <= x < 0x40 or 0x41 <= x < 0x5B or 0x61 <= x < 0x7B) else 0
    for x in range(256)
)


class MessageView(Blackboard):

    self_name = u'msg'

    def __init__(self, inner):
        super(MessageView, self).__init__()
        self.inner = inner
        self.rebuild_headers()
        self.annotations = {}

    version = property(lambda self: self.inner.version)
    header_entries = property(lambda self: self.inner.header_entries)
    body = property(lambda self: self.inner.body)
    trailer_entries = property(lambda self: self.inner.trailer_entries)

    @property
    def annotated_header_entries(self):
        return [(entry, self.annotations.get((False, i), [entry.value]))
                for i, entry in enumerate(self.header_entries)]

    @property
    def annotated_trailer_entries(self):
        return [(entry, self.annotations.get((True, i), [entry.value]))
                for i, entry in enumerate(self.trailer_entries)]

    def rebuild_headers(self):
        self.headers = HeadersView(self)

    @memoized_property
    def decoded_body(self):
        r = self.body
        codings = list(self.headers.content_encoding)
        while codings and okay(r) and r:
            coding = codings.pop()
            if coding in [cc.gzip, cc.x_gzip]:
                try:
                    r = decode_gzip(r)
                except Exception as e:
                    self.complain(1037, coding=coding, error=e)
                    r = Unparseable
            elif coding == cc.deflate:
                try:
                    r = decode_deflate(r)
                except Exception as e:
                    self.complain(1037, coding=coding, error=e)
                    r = Unparseable
            elif okay(coding):
                self.complain(1036, coding=coding)
                r = Unparseable
            else:
                r = Unparseable
        return r

    @property
    def full_content(self):
        return self.decoded_body

    @memoized_property
    def json_data(self):
        if not okay(self.full_content):
            return self.full_content
        ctype = self.headers.content_type
        if not ctype.is_okay or not media_type.is_json(ctype.value.item):
            return None
        try:
            s = self.full_content.decode('utf-8')
            return json.loads(s)
        except Exception as e:
            self.complain(1038, error=e)
            return Unparseable

    @memoized_property
    def xml_data(self):
        if not okay(self.full_content):
            return self.full_content
        ctype = self.headers.content_type
        if not ctype.is_okay or not media_type.is_xml(ctype.value.item):
            return None
        try:
            return defusedxml.ElementTree.fromstring(self.full_content)
        except defusedxml.DefusedXmlException:
            return Unparseable
        except Exception as e:
            self.complain(1039, error=e)
            return Unparseable

    @memoized_property
    def multipart_data(self):
        if not okay(self.full_content):
            return self.full_content
        ctype = self.headers.content_type
        if not ctype.is_okay or not media_type.is_multipart(ctype.value.item):
            return None
        multipart_code = (b'Content-Type: ' + ctype.entries[0].value + b'\r\n'
                          b'\r\n' + self.full_content)
        parsed = parse_email_message(multipart_code)
        for defect in parsed.defects:
            if isinstance(defect, email.errors.NoBoundaryInMultipartDefect):
                self.complain(1139)
            elif isinstance(defect, email.errors.StartBoundaryNotFoundDefect):
                self.complain(1140)
        return parsed if parsed.is_multipart() else Unparseable

    @memoized_property
    def url_encoded_data(self):
        if not okay(self.full_content):
            return self.full_content
        if not (self.headers.content_type ==
                media.application_x_www_form_urlencoded):
            return None
        for byte in six.iterbytes(self.full_content):
            if not URL_ENCODED_GOOD_BYTES[byte]:
                self.complain(1040, offending_value=byte)
                return Unparseable
        return parse_qs(self.full_content.decode('ascii'))

    @memoized_property
    def transformed(self):
        if warn.transformation_applied in self.headers.warning:
            self.complain(1189)
            return True
        return None


def check_message(msg):
    for hdr in msg.headers:
        # Force parsing every header present in the message
        # according to its syntax rules.
        _ = hdr.value
        if header.deprecated(hdr.name):
            msg.complain(1197, header=hdr)

    # Force checking the payload for various content types.
    _ = msg.json_data
    _ = msg.xml_data
    _ = msg.multipart_data
    _ = msg.url_encoded_data

    if msg.headers.trailer.is_present and \
            tc.chunked not in msg.headers.transfer_encoding:
        msg.complain(1054)

    for entry in msg.trailer_entries:
        if entry.name not in msg.headers.trailer:
            msg.complain(1030, header=entry)

    if msg.headers.transfer_encoding.is_present and \
            msg.headers.content_length.is_present:
        msg.complain(1020)

    for opt in msg.headers.connection.okay:
        if header.is_bad_for_connection(FieldName(opt)):
            msg.complain(1034, header=msg.headers[FieldName(opt)])

    if msg.headers.content_type.is_okay:
        if media_type.deprecated(msg.headers.content_type.value.item):
            msg.complain(1035)
        seen_params = set()
        for param_name, _ in msg.headers.content_type.value.param:
            if param_name in seen_params:
                msg.complain(1042, param=param_name)
            seen_params.add(param_name)

    if msg.headers.upgrade.is_present and \
            u'upgrade' not in msg.headers.connection:
        msg.complain(1050)

    if msg.headers.date > datetime.utcnow() + timedelta(seconds=10):
        msg.complain(1109)

    for warning in msg.headers.warning.okay:
        if warning.code < 100 or warning.code > 299:
            msg.complain(1163, code=warning.code)
        if okay(warning.date) and msg.headers.date != warning.date:
            msg.complain(1164, code=warning.code)

    if msg.transformed:
        if warn.transformation_applied not in msg.headers.warning:
            msg.complain(1191)
        if msg.headers.cache_control.no_transform:
            msg.complain(1192)

    for pragma in msg.headers.pragma.okay:
        if pragma != u'no-cache':
            msg.complain(1160, pragma=pragma.item)


def body_charset(msg):
    if msg.headers.content_type.is_okay:
        for name, value in msg.headers.content_type.value.param:
            if name == u'charset':
                return value


def parse_line_ending(stream):
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
        parse_line_ending(stream)
        entries.append(HeaderEntry(FieldName(name), value))
    parse_line_ending(stream)
    return entries


def parse_chunk(stream):
    size = stream.parse(rfc7230.chunk_size * skip(maybe(rfc7230.chunk_ext)))
    parse_line_ending(stream)
    if size == 0:
        return b''
    else:
        data = stream.consume_n_bytes(size)
        parse_line_ending(stream)
        return data


def parse_chunked(msg, stream):
    data = []
    try:
        with stream:
            chunk = parse_chunk(stream)
            while chunk:
                data.append(chunk)
                chunk = parse_chunk(stream)
            trailer = parse_header_fields(stream)
    except ParseError as e:
        stream.sane = False
        msg.complain(1005, error=e)
        msg.inner.body = Unparseable
    else:
        stream.dump_complaints(msg, u'chunked framing')
        msg.inner.body = b''.join(data)
        msg.inner.trailer_entries = trailer
        if trailer:
            msg.rebuild_headers()           # Rebuid the `HeadersView` cache


def decode_transfer_coding(msg, coding):
    if coding == tc.chunked:
        # The outermost chunked has already been peeled off at this point.
        msg.complain(1002)
        msg.inner.body = Unparseable
    elif coding in [tc.gzip, tc.x_gzip]:
        try:
            msg.inner.body = decode_gzip(msg.body)
        except Exception as e:
            msg.complain(1027, coding=coding, error=e)
            msg.inner.body = Unparseable
    elif coding == tc.deflate:
        try:
            msg.inner.body = decode_deflate(msg.body)
        except Exception as e:
            msg.complain(1027, coding=coding, error=e)
            msg.inner.body = Unparseable
    else:
        msg.complain(1003, coding=coding)
        msg.inner.body = Unparseable


def decode_gzip(data):
    return gzip.GzipFile(fileobj=io.BytesIO(data)).read()


def decode_deflate(data):
    return zlib.decompress(data)
