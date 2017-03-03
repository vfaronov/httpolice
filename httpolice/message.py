# -*- coding: utf-8; -*-

import codecs
from datetime import datetime, timedelta
import email.errors
from httpolice.util.moves import message_from_bytes as parse_email_message
import json
from six.moves.urllib.parse import parse_qs  # pylint: disable=import-error
import xml.etree.ElementTree

from bitstring import Bits
import defusedxml
import defusedxml.ElementTree
import six

from httpolice.blackboard import Blackboard, derived_property
from httpolice.codings import decode_brotli, decode_deflate, decode_gzip
from httpolice.header import HeadersView
from httpolice.known import cc, h, header, media, media_type, tc, upgrade, warn
from httpolice.parse import simple_parse
from httpolice.structure import (FieldName, HeaderEntry, HTTPVersion,
                                 Unavailable, http2, http11, okay)
from httpolice.syntax import rfc7230
from httpolice.util.text import force_unicode, format_chars, printable


# This list is taken from the HTML specification --
# http://www.w3.org/TR/html/forms.html#url-encoded-form-data --
# as the exhaustive list of bytes that can be output
# by a "conformant" URL encoder.

URL_ENCODED_GOOD_BYTES = Bits(
    1 if (x in [0x25, 0x26, 0x2A, 0x2B, 0x2D, 0x2E, 0x5F] or
          0x30 <= x < 0x40 or 0x41 <= x < 0x5B or 0x61 <= x < 0x7B) else 0
    for x in range(256)
)


class Message(Blackboard):

    """An HTTP message (request or response)."""

    self_name = u'msg'

    def __init__(self, version, header_entries, body, trailer_entries=None,
                 remark=None):
        super(Message, self).__init__()
        self.version = (HTTPVersion(force_unicode(version))
                        if version is not None else None)
        self.header_entries = [HeaderEntry(k, v)
                               for k, v in header_entries]
        self.body = bytes(body) if okay(body) else body
        self.trailer_entries = [HeaderEntry(k, v)
                                for k, v in trailer_entries or []]
        self.rebuild_headers()
        self.annotations = {}
        self.remark = remark

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
        codings = self.headers.content_encoding.value[:]
        while codings and okay(r) and r:
            coding = codings.pop()
            decoder = {cc.gzip: decode_gzip,
                       cc.x_gzip: decode_gzip,
                       cc.deflate: decode_deflate,
                       cc.br: decode_brotli}.get(coding)
            if decoder is not None:
                try:
                    r = decoder(r)
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
            charset = self.headers.content_type.param.get(u'charset', charset)

        try:
            codec = codecs.lookup(charset)
        except LookupError:
            return None
        charset = codec.name

        if okay(self.decoded_body):
            try:
                self.decoded_body.decode(charset)   # pylint: disable=no-member
            except UnicodeError:
                return None
        return charset

    @derived_property
    def unicode_body(self):
        if not okay(self.decoded_body):
            return self.decoded_body
        if self.guessed_charset is None:
            return Unavailable
        # pylint: disable=no-member
        return self.decoded_body.decode(self.guessed_charset)

    @derived_property
    def content_is_full(self):
        return True

    @derived_property
    def json_data(self):
        if self.headers.content_type.is_okay and \
                media_type.is_json(self.headers.content_type.item) and \
                okay(self.unicode_body) and self.content_is_full:
            try:
                r = json.loads(self.unicode_body)
            except ValueError as e:
                self.complain(1038, error=e)
                r = Unavailable
            else:
                if self.guessed_charset not in ['ascii', 'utf-8', 'utf-16',
                                                'utf-16-le', 'utf-16-be',
                                                'utf-32', 'utf-32-le',
                                                'utf-32-be']:
                    self.complain(1281)
            return r
        else:
            return None

    @derived_property
    def xml_data(self):
        if self.headers.content_type.is_okay and \
                media_type.is_xml(self.headers.content_type.item) and \
                okay(self.decoded_body) and self.content_is_full:
            try:
                # It's not inconceivable that a message might contain
                # maliciously constructed XML data, so we use `defusedxml`.
                return defusedxml.ElementTree.fromstring(self.decoded_body)
            except defusedxml.EntitiesForbidden:
                self.complain(1275)
                return Unavailable
            except xml.etree.ElementTree.ParseError as e:
                self.complain(1039, error=e)
                return Unavailable
        else:
            return None

    @derived_property
    def multipart_data(self):
        ctype = self.headers.content_type
        if ctype.is_okay and media_type.is_multipart(ctype.value.item) and \
                okay(self.decoded_body) and self.content_is_full:
            # All multipart media types obey the same general syntax
            # specified in RFC 2046 Section 5.1,
            # and should be parseable as email message payloads.
            multipart_code = (b'Content-Type: ' + ctype.entries[0].value +
                              b'\r\n\r\n' + self.decoded_body)
            parsed = parse_email_message(multipart_code)
            for d in parsed.defects:
                if isinstance(d, email.errors.NoBoundaryInMultipartDefect):
                    self.complain(1139)
                elif isinstance(d, email.errors.StartBoundaryNotFoundDefect):
                    self.complain(1140)
            return parsed if parsed.is_multipart() else Unavailable
        else:
            return None

    @derived_property
    def url_encoded_data(self):
        if self.headers.content_type == \
                media.application_x_www_form_urlencoded and \
                okay(self.decoded_body) and self.content_is_full:
            for byte in six.iterbytes(self.decoded_body):
                if not URL_ENCODED_GOOD_BYTES[byte]:
                    char = six.int2byte(byte)
                    self.complain(1040, char=format_chars([char]))
                    return Unavailable
            # pylint: disable=no-member
            return parse_qs(self.decoded_body.decode('ascii'))
        else:
            return None

    @derived_property
    def displayable_body(self):
        removing_te = [u'removing Transfer-Encoding'] \
            if self.headers.transfer_encoding else []
        removing_ce = [u'removing Content-Encoding'] \
            if self.headers.content_encoding else []
        decoding_charset = [u'decoding from %s' % self.guessed_charset] \
            if self.guessed_charset and self.guessed_charset != 'utf-8' else []
        pretty_printing = [u'pretty-printing']

        if okay(self.json_data):
            r = json.dumps(self.json_data, indent=2, ensure_ascii=False)
            transforms = \
                removing_te + removing_ce + decoding_charset + pretty_printing
        elif okay(self.unicode_body):
            r = self.unicode_body
            transforms = removing_te + removing_ce + decoding_charset
        elif okay(self.decoded_body):
            # pylint: disable=no-member
            r = self.decoded_body.decode('utf-8', 'replace')
            transforms = removing_te + removing_ce
        elif okay(self.body):
            r = self.body.decode('utf-8', 'replace')
            transforms = removing_te
        else:
            return self.body, []

        limit = 1000
        if len(r) > limit:
            r = r[:limit]
            transforms += [u'taking the first %d characters' % limit]

        pr = printable(r)
        if r != pr:
            r = pr
            transforms += [u'replacing non-printable characters '
                           u'with the \ufffd sign']

        return r, transforms

    @derived_property
    def transformed_by_proxy(self):
        if warn.transformation_applied in self.headers.warning:
            self.complain(1189)
            return True
        return None

    @derived_property
    def is_tls(self):
        raise NotImplementedError()


def check_message(msg):
    """Run all checks that apply to any message (both request and response)."""
    complain = msg.complain
    version = msg.version
    headers = msg.headers

    for hdr in headers:
        # Check the header name syntax.
        simple_parse(hdr.name, rfc7230.field_name,
                     complain, 1293, header=hdr, place=u'field name')
        # Force parsing every header present in the message
        # according to its syntax rules.
        _ = hdr.value
        if header.deprecated(hdr.name):
            complain(1197, header=hdr)
        if hdr.name.startswith(u'X-') and hdr.name not in h:    # not in known
            complain(1277, header=hdr)

    # Force checking the payload according to various rules.
    _ = msg.decoded_body
    _ = msg.unicode_body
    _ = msg.json_data
    _ = msg.xml_data
    _ = msg.multipart_data
    _ = msg.url_encoded_data

    if version == http11 and headers.trailer.is_present and \
            tc.chunked not in headers.transfer_encoding:
        # HTTP/2 supports trailers but has no notion of "chunked".
        complain(1054)

    for entry in msg.trailer_entries:
        if entry.name not in headers.trailer:
            complain(1030, header=entry)

    if headers.transfer_encoding.is_present and \
            headers.content_length.is_present:
        complain(1020)

    for opt in headers.connection:
        if header.is_bad_for_connection(FieldName(opt)):
            complain(1034, header=headers[FieldName(opt)])

    if headers.content_type.is_okay:
        if media_type.deprecated(headers.content_type.item):
            complain(1035)
        for dupe in headers.content_type.param.duplicates():
            complain(1042, param=dupe)

    if headers.content_type == media.application_json and \
            u'charset' in headers.content_type.param:
        complain(1280, header=headers.content_type)

    if headers.upgrade.is_present and u'upgrade' not in headers.connection:
        complain(1050)

    if headers.date > datetime.utcnow() + timedelta(seconds=10):
        complain(1109)

    for warning in headers.warning:
        if warning.code < 100 or warning.code > 299:
            complain(1163, code=warning.code)
        if okay(warning.date) and headers.date != warning.date:
            complain(1164, code=warning.code)

    if msg.transformed_by_proxy:
        if warn.transformation_applied not in headers.warning:
            complain(1191)
        if headers.cache_control.no_transform:
            complain(1192)

    for pragma in headers.pragma:
        if pragma != u'no-cache':
            complain(1160, pragma=pragma.item)

    if version == http2:
        for hdr in headers:
            if hdr.name in [h.connection, h.transfer_encoding, h.keep_alive]:
                complain(1244, header=hdr)
            elif hdr.name == h.upgrade:
                complain(1245)

    for protocol in headers.upgrade:
        if protocol.item == u'h2':
            complain(1228)
        if protocol.item == upgrade.h2c and msg.is_tls:
            complain(1233)
