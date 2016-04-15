# -*- coding: utf-8; -*-

import codecs
from datetime import datetime, timedelta
import email.errors
import json

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

from httpolice.blackboard import Blackboard, derived_property
from httpolice.codings import decode_deflate, decode_gzip
from httpolice.header import HeadersView
from httpolice.known import cc, header, media, media_type, tc, warn
from httpolice.structure import FieldName, Unavailable, okay


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

    @derived_property
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
                    r = Unavailable
            elif coding == cc.deflate:
                try:
                    r = decode_deflate(r)
                except Exception as e:
                    self.complain(1037, coding=coding, error=e)
                    r = Unavailable
            elif okay(coding):
                self.complain(1036, coding=coding)
                r = Unavailable
            else:
                r = Unavailable
        return r

    @derived_property
    def guessed_charset(self):
        charset = 'utf-8'
        if self.headers.content_type.is_okay:
            for (name, value) in self.headers.content_type.value.param:
                if name == u'charset':
                    charset = value

        try:
            codec = codecs.lookup(charset)
        except LookupError:
            return Unavailable
        charset = codec.name

        if okay(self.decoded_body):
            try:
                self.decoded_body.decode(charset)
            except UnicodeError:
                return Unavailable
        return charset

    @derived_property
    def unicode_body(self):
        if not okay(self.decoded_body):
            return self.decoded_body
        if not okay(self.guessed_charset):
            return self.guessed_charset
        return self.decoded_body.decode(self.guessed_charset)

    @derived_property
    def content_is_full(self):
        return True

    @derived_property
    def json_data(self):
        if not okay(self.unicode_body):
            return self.unicode_body
        if not self.content_is_full:
            return Unavailable
        ctype = self.headers.content_type
        if not ctype.is_okay or not media_type.is_json(ctype.value.item):
            return None
        try:
            return json.loads(self.unicode_body)
        except Exception as e:
            self.complain(1038, error=e)
            return Unavailable

    @derived_property
    def xml_data(self):
        if not okay(self.decoded_body):
            return self.decoded_body
        if not self.content_is_full:
            return Unavailable
        ctype = self.headers.content_type
        if not ctype.is_okay or not media_type.is_xml(ctype.value.item):
            return None
        try:
            return defusedxml.ElementTree.fromstring(self.decoded_body)
        except defusedxml.DefusedXmlException:
            return Unavailable
        except Exception as e:
            self.complain(1039, error=e)
            return Unavailable

    @derived_property
    def multipart_data(self):
        if not okay(self.decoded_body):
            return self.decoded_body
        if not self.content_is_full:
            return Unavailable
        ctype = self.headers.content_type
        if not ctype.is_okay or not media_type.is_multipart(ctype.value.item):
            return None
        multipart_code = (b'Content-Type: ' + ctype.entries[0].value + b'\r\n'
                          b'\r\n' + self.decoded_body)
        parsed = parse_email_message(multipart_code)
        for defect in parsed.defects:
            if isinstance(defect, email.errors.NoBoundaryInMultipartDefect):
                self.complain(1139)
            elif isinstance(defect, email.errors.StartBoundaryNotFoundDefect):
                self.complain(1140)
        return parsed if parsed.is_multipart() else Unavailable

    @derived_property
    def url_encoded_data(self):
        if not okay(self.decoded_body):
            return self.decoded_body
        if not self.content_is_full:
            return Unavailable
        if not (self.headers.content_type ==
                media.application_x_www_form_urlencoded):
            return None
        for byte in six.iterbytes(self.decoded_body):
            if not URL_ENCODED_GOOD_BYTES[byte]:
                self.complain(1040, offending_value=byte)
                return Unavailable
        return parse_qs(self.decoded_body.decode('ascii'))

    @derived_property
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
