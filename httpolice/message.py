# -*- coding: utf-8; -*-

from cStringIO import StringIO
import gzip
import json
import zlib

from httpolice import common, header_view, parse, syntax
from httpolice.common import Unparseable, okay
from httpolice.known import cc, header, media_type, tc


class Message(common.ReportNode):

    self_name = 'msg'

    def __init__(self, version, header_entries,
                 body=None, trailer_entries=None, raw=None):
        super(Message, self).__init__()
        self.version = version
        self.header_entries = header_entries
        self.body = body
        self.trailer_entries = trailer_entries
        self.raw = raw
        self.rebuild_headers()
        self._decoded_body = None

    def rebuild_headers(self):
        self.headers = header_view.HeadersView(self)

    @property
    def decoded_body(self):
        if self._decoded_body is None:
            self._decode_body()
        return self._decoded_body

    def _decode_body(self):
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
        self._decoded_body = r


def check_message(msg):
    # Force parsing every header present in the message according to its rules.
    for entry in msg.header_entries + (msg.trailer_entries or []):
        _ = msg.headers[entry.name].value

    data = msg.decoded_body
    if okay(data) and msg.headers.content_type.is_okay:
        check_media(msg, msg.headers.content_type.value.item, data)

    for entry in msg.trailer_entries or []:
        if entry.name not in msg.headers.trailer:
            msg.complain(1030, header=entry)

    if msg.headers.transfer_encoding and msg.headers.content_length.is_present:
        msg.complain(1020)

    for opt in msg.headers.connection:
        if okay(opt) and header.is_bad_for_connection(common.FieldName(opt)):
            msg.complain(1034, header=msg.headers[common.FieldName(opt)])

    if msg.headers.content_type.is_okay and \
            media_type.deprecated(msg.headers.content_type.value.item):
        msg.complain(1035)


def check_media(msg, type_, data):
    if media_type.is_json(type_):
        try:
            json.loads(data)
        except Exception, e:
            msg.complain(1038, error=e)


def parse_chunked(msg, state):
    data = []
    try:
        chunk = syntax.chunk.parse(state)
        while chunk:
            data.append(chunk)
            chunk = syntax.chunk.parse(state)
        trailer = syntax.trailer_part.parse(state)
        syntax.crlf.parse(state)
    except parse.ParseError, e:
        msg.complain(1005, error=e)
        msg.body = Unparseable
        state.sane = False
    else:
        msg.body = ''.join(data)
        msg.trailer_entries = trailer
        if trailer:
            msg.rebuild_headers()           # Rebuid the `HeadersView` cache


def decode_transfer_coding(msg, coding):
    if coding == tc.chunked:
        # The outermost chunked has already been peeled off at this point.
        msg.complain(1002)
        msg.body = Unparseable
    elif coding in [tc.gzip, tc.x_gzip]:
        try:
            msg.body = decode_gzip(msg.body)
        except Exception, e:
            msg.complain(1027, coding=coding, error=e)
            msg.body = Unparseable
    elif coding == tc.deflate:
        try:
            msg.body = decode_deflate(msg.body)
        except Exception, e:
            msg.complain(1027, coding=coding, error=e)
            msg.body = Unparseable
    else:
        msg.complain(1003, coding=coding)
        msg.body = Unparseable


def decode_gzip(data):
    return gzip.GzipFile(fileobj=StringIO(data)).read()


def decode_deflate(data):
    return zlib.decompress(data)
