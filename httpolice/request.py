# -*- coding: utf-8; -*-

from httpolice import message
from httpolice.common import http11
from httpolice.known import h, method, tc


class Request(message.Message):

    def __repr__(self):
        return '<Request %s>' % self.method

    def __init__(self, method_, target, version_, header_entries,
                 body=None, trailer_entries=None, raw=None):
        super(Request, self).__init__(version_, header_entries,
                                      body, trailer_entries, raw)
        self.method = method_
        self.target = target


def check_request(req):
    message.check_message(req)

    if (method.defines_body(req.method) and
            req.headers.content_length.is_absent and
            req.headers.transfer_encoding.is_absent):
        req.complain(1021)

    if (method.defines_body(req.method) == False) and (not req.body) and \
            req.headers.content_length.is_present:
        req.complain(1022)

    if tc.chunked in req.headers.te:
        req.complain(1028)

    if req.headers.te and u'TE' not in req.headers.connection:
        req.complain(1029)

    if req.version == http11:
        if req.headers.host.is_absent:
            req.complain(1031)
        elif req.header_entries[0].name != h.host:
            req.complain(1032)
