# -*- coding: utf-8; -*-

from httpolice import header_view, parse, syntax
from httpolice.common import Unparseable


class Message(object):

    def __init__(self, report, version, header_entries,
                 stream=None, body=None):
        self.report = report
        self.version = version
        self.header_entries = header_entries
        self.stream = stream
        self.body = body
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
        for i, entry in enumerate(trailers, 1):
            entry.position = -i
            msg.header_entries.append(entry)
        return True
