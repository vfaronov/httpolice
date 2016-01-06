# -*- coding: utf-8; -*-

from httpolice import message, parse, syntax, transfer_coding
from httpolice.common import Unparseable
from httpolice.transfer_coding import known_codings as tc


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
            entries = parse.many(syntax.header_field +
                                 parse.ignore(syntax.crlf)).parse(state)
            for i, entry in enumerate(entries):
                entry.position = i
            syntax.crlf.parse(state)
        except parse.ParseError:
            reqs.append(Unparseable)
            return reqs
        req = Request(report, meth, targ, ver, entries, stream, was_tls)
        req.body = Unparseable
        reqs.append(req)

        # RFC 7230 section 3.3.3
        if req.headers.transfer_encoding:
            codings = list(req.headers.transfer_encoding)
            if codings.pop().item == tc.chunked:
                if not message.parse_chunked(req, state):
                    return reqs
            else:
                return reqs
            while codings and (req.body is not Unparseable):
                req.body = transfer_coding.decode(req.body, codings.pop())
        elif req.headers.content_length:
            n = req.headers.content_length.value
            if n is Unparseable:
                return reqs
            try:
                req.body = parse.nbytes(n, n).parse(state)
            except parse.ParseError:
                return reqs
        else:
            req.body = ''

    return reqs
