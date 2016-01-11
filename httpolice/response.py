# -*- coding: utf-8; -*-

from httpolice import message
from httpolice.common import Unparseable, http11, okay
from httpolice.known import h, m, st, tc


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
    elif not resp.status.informational and resp.status != st.no_content:
        if resp.headers.content_length.is_absent and \
                tc.chunked not in resp.headers.transfer_encoding and \
                resp.version == http11:
            resp.complain(1025)
            if u'close' not in resp.headers.connection:
                resp.complain(1047)

    if req.version == http11 and (req.headers.host.is_absent or
                                  req.headers.host.value is Unparseable or
                                  len(req.headers.enumerate(h.host)) > 1):
        if resp.status.successful or resp.status.redirection:
            resp.complain(1033)

    if req.is_to_proxy and resp.headers.via.is_absent and \
            not resp.status.informational and \
            resp.status != st.proxy_authentication_required:
        resp.complain(1046)


def check_responses_flow(resps):
    pass
