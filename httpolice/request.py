# -*- coding: utf-8; -*-

from httpolice import common, message, parse, syntax


class Request(message.Message):

    def __repr__(self):
        return '<Request>'

    def __init__(self, report, meth, targ, ver, header_entries,
                 stream=None, was_tls=None, body=None):
        super(Request, self).__init__(report, ver, header_entries, stream,
                                      body)
        self.method = meth
        self.target = targ
        self.was_tls = was_tls


def parse_stream(stream, report, was_tls=None):
    state = parse.State(stream)
    reqs = []
    while not state.is_eof():
        try:
            (meth, targ, ver) = syntax.request_line.parse(state)
            entries = parse.many(syntax.header_field).parse(state)
            for i, entry in enumerate(entries):
                entry.position = i
            syntax.crlf.parse(state)
        except parse.ParseError:
            reqs.append(common.Unparseable)
            return reqs
        req = Request(report, meth, targ, ver, entries, stream, was_tls)
        reqs.append(req)
        if req.headers.content_length.is_present:
            n = req.headers.content_length.value
            try:
                req.body = parse.nbytes(n, n).parse(state)
            except parse.ParseError:
                req.body = common.Unparseable
                return reqs
    return reqs
