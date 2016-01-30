# -*- coding: utf-8; -*-

from cStringIO import StringIO
from datetime import datetime, timedelta
import email
import email.errors
import gzip
import json
import urlparse
import zlib

import defusedxml
import defusedxml.ElementTree

from httpolice import parse
from httpolice.blackboard import Blackboard, memoized_property
from httpolice.header import HeadersView
from httpolice.known import cc, header, media, media_type, tc, warn
from httpolice.structure import FieldName, Unparseable, okay
from httpolice.syntax import rfc7230
from httpolice.syntax.common import crlf


class MessageView(Blackboard):

    self_name = 'msg'

    def __init__(self, inner):
        super(MessageView, self).__init__()
        self.inner = inner
        self.rebuild_headers()
        self.annotations = {}

    version = property(lambda self: self.inner.version)
    header_entries = property(lambda self: self.inner.header_entries)
    body = property(lambda self: self.inner.body)
    trailer_entries = property(lambda self: self.inner.trailer_entries)
    raw = property(lambda self: self.inner.raw)

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
        while codings and okay(r):
            coding = codings.pop()
            if coding in [cc.gzip, cc.x_gzip]:
                try:
                    r = decode_gzip(r)
                except Exception, e:
                    self.complain(1037, coding=coding, error=e)
                    r = Unparseable
            elif coding == cc.deflate:
                try:
                    r = decode_deflate(r)
                except Exception, e:
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
            return json.loads(self.full_content)
        except Exception, e:
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
        except Exception, e:
            self.complain(1039, error=e)
            return Unparseable

    @memoized_property
    def multipart_data(self):
        if not okay(self.full_content):
            return self.full_content
        ctype = self.headers.content_type
        if not ctype.is_okay or not media_type.is_multipart(ctype.value.item):
            return None
        multipart_code = ('Content-Type: ' + ctype.entries[0].value + '\r\n'
                          '\r\n' + self.full_content)
        parsed = email.message_from_string(multipart_code)
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
        # This list is taken from the HTML specification --
        # http://www.w3.org/TR/html/forms.html#url-encoded-form-data --
        # as the exhaustive list of bytes that can be output
        # by a "conformant" URL encoder.
        good_bytes = ([0x25, 0x26, 0x2A, 0x2B, 0x2D, 0x2E, 0x5F] +
                      range(0x30, 0x40) + range(0x41, 0x5B) +
                      range(0x61, 0x7B))
        for byte in self.full_content:
            if ord(byte) not in good_bytes:
                self.complain(1040, offending_value=hex(ord(byte)))
                return Unparseable
        return urlparse.parse_qs(self.full_content)

    @memoized_property
    def transformed(self):
        if warn.transformation_applied in self.headers.warning:
            self.complain(1189)
            return True
        return None


def check_message(msg):
    # Force parsing every header present in the message according to its rules.
    for hdr in msg.headers:
        _ = hdr.value

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
        if warning.date and msg.headers.date != warning.date:
            msg.complain(1164, code=warning.code)

    if msg.transformed:
        if warn.transformation_applied not in msg.headers.warning:
            msg.complain(1191)
        if msg.headers.cache_control.no_transform:
            msg.complain(1192)


def body_charset(msg):
    if msg.headers.content_type.is_okay:
        for name, value in msg.headers.content_type.value.param:
            if name == u'charset':
                return value


def parse_chunked(msg, state):
    data = []
    try:
        saved = state.save()
        chunk = rfc7230.chunk.parse(state)
        while chunk:
            data.append(chunk)
            chunk = rfc7230.chunk.parse(state)
        trailer = rfc7230.trailer_part.parse(state)
        crlf.parse(state)
    except parse.ParseError, e:
        state.restore(saved)
        state.sane = False
        msg.complain(1005, error=e)
        msg.inner.body = Unparseable
    else:
        state.dump_complaints(msg, u'chunked framing')
        msg.inner.body = ''.join(data)
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
        except Exception, e:
            msg.complain(1027, coding=coding, error=e)
            msg.inner.body = Unparseable
    elif coding == tc.deflate:
        try:
            msg.inner.body = decode_deflate(msg.body)
        except Exception, e:
            msg.complain(1027, coding=coding, error=e)
            msg.inner.body = Unparseable
    else:
        msg.complain(1003, coding=coding)
        msg.inner.body = Unparseable


def decode_gzip(data):
    return gzip.GzipFile(fileobj=StringIO(data)).read()


def decode_deflate(data):
    return zlib.decompress(data)
