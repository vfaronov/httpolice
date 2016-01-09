# -*- coding: utf-8; -*-

from httpolice import message
from httpolice.common import okay
from httpolice.known import m, st


class Response(message.Message):

    def __repr__(self):
        return '<Response %d>' % self.status

    def __init__(self, version, status, header_entries,
                 body=None, trailer_entries=None, reason=None, raw=None):
        super(Response, self).__init__(version, header_entries,
                                       body, trailer_entries, raw)
        self.status = status
        self.reason = reason
        self.request = None


def check_responses(resps):
    for resp in resps:
        if okay(resp):
            check_response(resp)
    if all(okay(resp) for resp in resps):
        check_responses_flow(resps)


def check_response(resp):
    check_response_itself(resp)
    if okay(resp.request):
        check_response_in_context(resp, resp.request)


def check_response_itself(resp):
    message.check_message(resp)

    if resp.status.informational or resp.status == st.no_content:
        if resp.headers.transfer_encoding.is_present:
            resp.complain(1018)
        if resp.headers.content_length.is_present:
            resp.complain(1023)


def check_response_in_context(resp, req):
    if req.method == m.CONNECT and resp.status.successful:
        if resp.headers.transfer_encoding.is_present:
            resp.complain(1019)
        if resp.headers.content_length.is_present:
            resp.complain(1024)


def check_responses_flow(resps):
    pass
