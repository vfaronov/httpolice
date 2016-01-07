# -*- coding: utf-8; -*-

from httpolice import header_view, parse, syntax
from httpolice.common import Unparseable


class Message(object):

    def __init__(self, version, header_entries,
                 body=None, trailer_entries=None, raw=None):
        self.version = version
        self.header_entries = header_entries
        self.body = body
        self.trailer_entries = trailer_entries
        self.raw = raw
        self.headers = header_view.HeadersView(self)


def parse_chunked(msg, state):
    data = []
    try:
        chunk = syntax.chunk.parse(state)
        while chunk:
            data.append(chunk)
            chunk = syntax.chunk.parse(state)
        trailers = syntax.trailer_part.parse(state)
        syntax.crlf.parse(state)
    except parse.ParseError:
        msg.body = Unparseable
        return False
    else:
        msg.body = ''.join(data)
        msg.trailer_entries = trailers
        return True
