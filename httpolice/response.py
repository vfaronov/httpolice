# -*- coding: utf-8; -*-

from httpolice import message
from httpolice.common import Unparseable, http10, http11, okay, url_equals
from httpolice.known import h, header, m, method, st, tc

import urlparse


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

    for hdr in resp.headers:
        if header.is_for_response(hdr.name) == False:
            resp.complain(1064, header=hdr)
        elif header.is_representation_metadata(hdr.name) and \
                resp.status.informational:
            resp.complain(1052, header=hdr)

    if resp.status == st.switching_protocols and \
            resp.headers.upgrade.is_absent:
        resp.complain(1048)

    if resp.status == st.non_authoritative_information and \
            resp.headers.via.is_absent:
        resp.complain(1075)

    if resp.status == st.reset_content and resp.body:
        resp.complain(1076)

    if resp.headers.location.is_absent:
        if resp.status == st.moved_permanently:
            resp.complain(1078)
        elif resp.status == st.found:
            resp.complain(1079)
        elif resp.status == st.see_other:
            resp.complain(1080)
        elif resp.status == st.temporary_redirect:
            resp.complain(1084)

    if resp.status == st.use_proxy:
        resp.complain(1082)
    elif resp.status == 306:
        resp.complain(1083)
    elif resp.status == st.payment_required:
        resp.complain(1088)

    if resp.status == st.method_not_allowed:
        if resp.headers.allow.is_absent:
            resp.complain(1089)

    if resp.status == st.request_timeout and \
            u'close' not in resp.headers.connection:
        resp.complain(1094)


def check_response_in_context(resp, req):
    if req.method == m.CONNECT and resp.status.successful:
        if resp.headers.transfer_encoding.is_present:
            resp.complain(1019)
        if resp.headers.content_length.is_present:
            resp.complain(1024)
    elif not resp.status.informational and \
            resp.status not in [st.no_content, st.not_modified] and \
            resp.headers.content_length.is_absent and \
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

    if req.is_absolute_form and resp.headers.via.is_absent and \
            not resp.status.informational and \
            resp.status != st.proxy_authentication_required:
        resp.complain(1046)

    if resp.status == st.switching_protocols:
        if any(proto not in req.headers.upgrade
               for proto in resp.headers.upgrade):
            resp.complain(1049)
        if req.version == http10:
            resp.complain(1051)
    elif resp.status.informational and req.version == http10:
        resp.complain(1071)

    if resp.headers.content_location.is_okay and req.effective_uri:
        absolute_content_location = urlparse.urljoin(
            req.effective_uri, resp.headers.content_location.value)
        if url_equals(req.effective_uri, absolute_content_location):
            if req.method in [m.GET, m.HEAD] and resp.status in [
                    st.ok, st.non_authoritative_information,
                    st.no_content, st.partial_content,
                    st.not_modified]:
                resp.complain(1055)
            elif req.method == m.DELETE:
                resp.complain(1060)

    if resp.headers.location.is_okay and req.effective_uri and req.scheme:
        location = urlparse.urljoin(req.effective_uri,
                                    resp.headers.location.value)
        if url_equals(req.effective_uri, location):
            if resp.status in [st.multiple_choices, st.temporary_redirect]:
                resp.complain(1085)
            if resp.status in [st.moved_permanently, st.found, st.see_other] \
                    and req.method != m.POST:
                resp.complain(1085)

    if req.method == m.PUT and req.headers.content_range.is_present and \
            resp.status.successful:
        resp.complain(1058)

    if method.is_safe(req.method):
        if resp.status == st.created:
            resp.complain(1072)
        elif resp.status == st.accepted:
            resp.complain(1074)
        elif resp.status == st.conflict:
            resp.complain(1095)

    if resp.status == st.created and req.method == m.POST and \
            resp.headers.location.is_absent:
        resp.complain(1073)

    if req.method != m.HEAD and not resp.body:
        if resp.status == st.multiple_choices:
            resp.complain(1077)
        elif resp.status == st.see_other:
            resp.complain(1081)
        elif resp.status == st.not_acceptable:
            resp.complain(1092)
        elif resp.status == st.conflict:
            resp.complain(1096)
        elif resp.status.client_error:
            resp.complain(1087)
        elif resp.status.server_error:
            resp.complain(1104)

    if req.method == m.OPTIONS and req.is_asterisk_form and \
            resp.status in [st.multiple_choices, st.moved_permanently,
                            st.found, st.temporary_redirect]:
        resp.complain(1086)

    if resp.status == st.not_acceptable:
        if all(header.is_proactive_conneg(hdr.name) == False
               for hdr in req.headers):
            resp.complain(1090)
        elif not any(header.is_proactive_conneg(hdr.name)
                     for hdr in req.headers):
            resp.complain(1091)

    if resp.status == st.length_required and \
            req.headers.content_length.is_okay:
        resp.complain(1097)

    if not req.body:
        if resp.status == st.payload_too_large:
            resp.complain(1098)
        elif resp.status == st.unsupported_media_type:
            resp.complain(1099)

    if resp.status == st.expectation_failed and req.headers.expect.is_absent:
        resp.complain(1100)

    for proto in resp.headers.upgrade:
        if okay(proto) and proto in req.headers.upgrade:
            if resp.status == st.upgrade_required:
                resp.complain(1102, protocol=proto)
            elif resp.status.successful:
                resp.complain(1103, protocol=proto)
            break

    if resp.status == st.upgrade_required and not resp.headers.upgrade:
        resp.complain(1101)
