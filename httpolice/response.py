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

    status = resp.status
    headers = resp.headers
    body = resp.body

    if status.informational or status == st.no_content:
        if headers.transfer_encoding.is_present:
            resp.complain(1018)
        if headers.content_length.is_present:
            resp.complain(1023)

    for hdr in headers:
        if header.is_for_response(hdr.name) == False:
            resp.complain(1064, header=hdr)
        elif header.is_representation_metadata(hdr.name) and \
                status.informational:
            resp.complain(1052, header=hdr)

    if status == st.switching_protocols and headers.upgrade.is_absent:
        resp.complain(1048)

    if status == st.non_authoritative_information and headers.via.is_absent:
        resp.complain(1075)

    if status == st.reset_content and body:
        resp.complain(1076)

    if headers.location.is_absent:
        if status == st.moved_permanently:
            resp.complain(1078)
        elif status == st.found:
            resp.complain(1079)
        elif status == st.see_other:
            resp.complain(1080)
        elif status == st.temporary_redirect:
            resp.complain(1084)

    if status == st.use_proxy:
        resp.complain(1082)
    elif status == 306:
        resp.complain(1083)
    elif status == st.payment_required:
        resp.complain(1088)

    if status == st.method_not_allowed:
        if headers.allow.is_absent:
            resp.complain(1089)

    if status == st.request_timeout and u'close' not in headers.connection:
        resp.complain(1094)

    if headers.date.is_absent and (status.successful or status.redirection or
                                   status.client_error):
        resp.complain(1110)

    if headers.location.is_present:
        if status == st.created:
            if headers.location.is_okay and \
                    urlparse.urlparse(headers.location.value).fragment:
                resp.complain(1111)
        elif not status.redirection:
            resp.complain(1112)

    if headers.retry_after.is_present and \
            not status.redirection and \
            status not in [st.payload_too_large, st.service_unavailable]:
        resp.complain(1113)

    if headers.date < headers.last_modified:
        resp.complain(1118)

    if status == st.not_modified:
        for hdr in headers:
            if hdr.name == h.etag:
                continue
            elif hdr.name == h.last_modified:
                if headers.etag.is_present:
                    resp.complain(1127, header=hdr)
            elif header.is_representation_metadata(hdr.name):
                resp.complain(1127, header=hdr)


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

    if req.version == http11 and (not req.headers.host.is_okay or
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
        elif resp.status == st.http_version_not_supported:
            resp.complain(1106)
        elif resp.status.server_error:
            resp.complain(1104)

    if req.method == m.OPTIONS and req.is_asterisk_form and \
            resp.status in [st.multiple_choices, st.moved_permanently,
                            st.found, st.temporary_redirect]:
        resp.complain(1086)

    if resp.status == st.not_acceptable:
        all_headers = set(h.name for h in req.headers)
        known_conneg = set(h.name for h in req.headers
                           if header.is_proactive_conneg(h.name) == True)
        known_not_conneg = set(h.name for h in req.headers
                               if header.is_proactive_conneg(h.name) == False)
        if known_not_conneg == all_headers:
            resp.complain(1090)
        elif not known_conneg:
            resp.complain(1091)
        elif known_conneg == set([h.accept_language]):
            resp.complain(1117)

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

    if resp.status == st.http_version_not_supported and \
            resp.version == req.version:
        resp.complain(1105)

    if resp.status == st.method_not_allowed:
        if req.method in resp.headers.allow:
            resp.complain(1114)
    elif resp.status.successful:
        if resp.headers.allow.is_present and \
                req.method not in resp.headers.allow:
            resp.complain(1115)

    if req.method in [m.GET, m.HEAD] and resp.status.successful:
        if req.headers.if_none_match.is_okay and resp.headers.etag.is_okay:
            if req.headers.if_none_match == u'*':
                # In this case we could ignore the presence of ``ETag``,
                # but then we would need a separate notice
                # that would be pretty useless and too hard to explain.
                resp.complain(1121)
            elif any(tag.weak_equiv(resp.headers.etag.value)
                     for tag in req.headers.if_none_match.value):
                resp.complain(1121)

        elif req.headers.if_modified_since >= resp.headers.last_modified:
            resp.complain(1123)

    if resp.status in [st.not_modified, st.precondition_failed]:
        all_headers = set(h.name for h in req.headers)
        known_precond = set(h.name for h in req.headers
                            if header.is_precondition(h.name) == True)
        known_not_precond = set(h.name for h in req.headers
                                if header.is_precondition(h.name) == False)

        if req.method not in [m.GET, m.HEAD] and \
                resp.status == st.not_modified:
            resp.complain(1124)
        elif known_not_precond == all_headers:
            resp.complain(1125)
        elif not known_precond:
            resp.complain(1126)
        elif known_precond == set([h.if_modified_since]):
            if req.method not in [m.GET, m.HEAD]:
                resp.complain(1128)
        elif known_precond.issubset(set([h.if_match, h.if_none_match,
                                         h.if_modified_since,
                                         h.if_unmodified_since, h.if_range])):
            if req.method in [m.CONNECT, m.OPTIONS, m.TRACE]:
                resp.complain(1129)

    if resp.status == st.partial_content:
        if req.headers.range.is_absent:
            resp.complain(1136)
        elif req.method != m.GET:
            resp.complain(1137)
