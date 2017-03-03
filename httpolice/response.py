# -*- coding: utf-8; -*-

from datetime import datetime, timedelta
from six.moves.urllib.parse import urljoin  # pylint: disable=import-error
from six.moves.urllib.parse import urlparse  # pylint: disable=import-error

import six

from httpolice import message
from httpolice.blackboard import derived_property
from httpolice.known import (auth, cache, cache_directive, h, header, hsts, m,
                             media, media_type, method as method_info, rel, st,
                             status_code, tc, unit, upgrade, warn)
from httpolice.known.status_code import NOT_AT_ALL, NOT_BY_DEFAULT
from httpolice.parse import simple_parse
from httpolice.structure import (EntityTag, StatusCode, http2, http10, http11,
                                 okay)
from httpolice.syntax import rfc6749, rfc7230
from httpolice.util.data import duplicates
from httpolice.util.text import (contains_percent_encodes, force_unicode,
                                 is_ascii)


class Response(message.Message):

    def __init__(self, version, status, reason, header_entries,
                 body, trailer_entries=None, remark=None):
        """
        :param version:
            The response's protocol version, as a Unicode string,
            or `None` if unknown (this disables some checks).

            For responses sent over HTTP/1.x connections,
            this should be the HTTP version sent in the `status line`__,
            such as ``u'HTTP/1.0'`` or ``u'HTTP/1.1'``.

            __ https://tools.ietf.org/html/rfc7230#section-3.1.2

            For responses sent over HTTP/2 connections,
            this should be ``u'HTTP/2'``.

        :param status:
            The response's status code, as an integer.

        :param reason:
            The response's reason phrase (such as "OK" or "Not Found"),
            as a Unicode string, or `None` if unknown (as in HTTP/2).

        :param header_entries:
            A list of the response's headers (may be empty).
            It must **not** include HTTP/2 `pseudo-headers`__.

            __ https://tools.ietf.org/html/rfc7540#section-8.1.2.1

            Every item of the list must be a ``(name, value)`` pair.

            `name` must be a Unicode string.

            `value` may be a byte string or a Unicode string.
            If it is Unicode, HTTPolice will assume that it has been decoded
            from ISO-8859-1 (the historic encoding of HTTP),
            and will encode it back into ISO-8859-1 before any processing.

        :param body:
            The response's payload body, as a **byte string**,
            or `None` if unknown (this disables some checks).

            If the response has no payload (like 204 or 304 responses),
            this should be the empty string ``b''``.

            This must be the payload body as `defined by RFC 7230`__:
            **after** removing any ``Transfer-Encoding`` (like ``chunked``),
            but **before** removing any ``Content-Encoding`` (like ``gzip``).

            __ https://tools.ietf.org/html/rfc7230#section-3.3

        :param trailer_entries:
            A list of headers from the response's trailer part
            (as found in `chunked coding`__ or `HTTP/2`__),
            or `None` if there is no trailer part.

            __ https://tools.ietf.org/html/rfc7230#section-4.1.2
            __ https://tools.ietf.org/html/rfc7540#section-8.1

            The format is the same as for `header_entries`.

        :param remark:
            If not `None`, this Unicode string will be shown
            above this response in HTML reports
            (when the appropriate option is enabled).
            For example, it can be used to identify the source of the data:
            ``u'from somefile.dat, offset 1337'``.

        """
        super(Response, self).__init__(version, header_entries,
                                       body, trailer_entries, remark)
        self.status = StatusCode(status)
        self.reason = force_unicode(reason) if reason is not None else None
        self.request = None

    def __repr__(self):
        return '<Response %d>' % self.status

    @derived_property
    def content_is_full(self):
        if self.status == st.not_modified:
            return False
        if self.status == st.partial_content and \
                self.headers.content_type != media.multipart_byteranges:
            return False
        if okay(self.request):
            return self.request.method != m.HEAD
        if self.body:
            return True
        return None         # pragma: no cover

    @derived_property
    def from_cache(self):
        if self.headers.date.is_okay and self.headers.age.is_okay:
            date = self.headers.date.value
            age = timedelta(seconds=self.headers.age.value)
            if date + age > datetime.utcnow() + timedelta(seconds=30):
                self.complain(1241)
                return None

        if self.headers.age.is_present:
            self.complain(1168)
            return True

        for warning in self.headers.warning:
            if 100 <= warning.code < 200:
                self.complain(1169, code=warning.code)
                return True

        return None

    @derived_property
    def heuristic_expiration(self):
        if not self.from_cache:
            return self.from_cache
        if warn.heuristic_expiration in self.headers.warning:
            self.complain(1179)
            return True
        if self.headers.expires.is_present:
            return False
        if self.headers.cache_control.max_age:
            return False
        elif self.headers.cache_control.is_absent:
            self.complain(1178)
            return True
        return None

    @derived_property
    def stale(self):
        for code in [warn.response_is_stale, warn.revalidation_failed]:
            if code in self.headers.warning:
                self.complain(1183, code=code)
                return True
        # We can't know if the response comes from a shared cache,
        # so we just skip this if there is special expiration time for those.
        if self.headers.cache_control.s_maxage is None:
            if self.headers.age > self.headers.cache_control.max_age:
                self.complain(1184)
                return True
            if self.headers.cache_control.max_age is None and \
                    self.headers.expires.is_okay and self.headers.date.is_okay:
                delta = self.headers.expires.value - self.headers.date.value
                if self.headers.age > delta.total_seconds():
                    self.complain(1185)
                    return True
        return None

    @derived_property
    def transformed_by_proxy(self):
        if self.status == st.non_authoritative_information:
            self.complain(1190)
            return True
        return super(Response, self).transformed_by_proxy

    @derived_property
    def is_tls(self):
        if okay(self.request):
            return self.request.is_tls
        else:   # pragma: no cover
            return None


def check_responses(resps):
    for resp in resps:
        check_response(resp)


def check_response(resp):
    """Apply all checks to the response `resp`."""
    check_response_itself(resp)
    if resp.request:
        check_response_in_context(resp, resp.request)


def check_response_itself(resp):
    resp.silence(notice_id
                 for (notice_id, _) in resp.headers.httpolice_silence)

    message.check_message(resp)

    complain = resp.complain
    version = resp.version
    status = resp.status
    headers = resp.headers
    body = resp.body

    # Check syntax of reason phrase.
    if okay(resp.reason):
        simple_parse(resp.reason, rfc7230.reason_phrase,
                     complain, 1294, place=u'reason phrase')

    if not (100 <= status <= 599):
        complain(1167)

    if status.informational and u'close' in headers.connection:
        complain(1198)

    if status.informational or status == st.no_content:
        if headers.transfer_encoding.is_present:
            complain(1018)
        if headers.content_length.is_present:
            complain(1023)

    for hdr in headers:
        if header.is_for_response(hdr.name) == False:
            complain(1064, header=hdr)
        elif header.is_representation_metadata(hdr.name) and \
                status.informational:
            complain(1052, header=hdr)

    if status == st.switching_protocols:
        if headers.upgrade.is_absent:
            complain(1048)
        if version == http2:
            complain(1246)

    if status == st.no_content and body:
        complain(1240)

    if status == st.reset_content and body:
        complain(1076)

    if headers.location.is_absent:
        if status == st.moved_permanently:
            complain(1078)
        if status == st.found:
            complain(1079)
        if status == st.see_other:
            complain(1080)
        if status == st.temporary_redirect:
            complain(1084)
        if status == st.permanent_redirect:
            complain(1205)

    if status == st.use_proxy:
        complain(1082)
    if status == 306:
        complain(1083)
    if status == st.payment_required:
        complain(1088)

    if status == st.method_not_allowed and headers.allow.is_absent:
        complain(1089)

    if status == st.request_timeout and u'close' not in headers.connection:
        complain(1094)

    if headers.date.is_absent and (status.successful or status.redirection or
                                   status.client_error):
        complain(1110)

    if status == st.created and headers.location.is_okay and \
            urlparse(headers.location.value).fragment:
        complain(1111)

    if headers.location.is_present and \
            not status.redirection and status != st.created:
        complain(1112)

    if headers.retry_after.is_present and \
            not status.redirection and \
            status not in [st.payload_too_large, st.service_unavailable,
                           st.too_many_requests]:
        complain(1113)

    if headers.date < headers.last_modified.value:
        complain(1118)

    if status == st.not_modified:
        for hdr in headers:
            # RFC 7232 says "Last-Modified might be useful
            # if the response does not have an ETag field",
            # but really it doesn't hurt even if there is an ETag,
            # and this is widely seen in practice.
            if hdr.name in [h.etag, h.last_modified]:
                continue
            elif header.is_representation_metadata(hdr.name):
                complain(1127, header=hdr)

    if headers.content_range.is_present and \
            status not in [st.partial_content, st.range_not_satisfiable]:
        complain(1147)

    if status == st.partial_content:
        if headers.content_type == media.multipart_byteranges:
            _check_multipart_byteranges(resp)
            if headers.content_range.is_present:
                complain(1143)
        elif headers.content_range.is_absent:
            complain(1138)

    for direct in headers.cache_control:
        if cache_directive.is_for_response(direct.item) == False:
            complain(1153, directive=direct.item)

    if u'no-cache' in headers.pragma:
        complain(1162)

    if resp.from_cache:
        if headers.age.is_absent:
            complain(1166)
        if headers.cache_control.no_cache in [True, []]:
            complain(1175)
        if headers.cache_control.no_store:
            complain(1176)

        if status_code.is_cacheable(status) == NOT_AT_ALL:
            complain(1202)
        elif status_code.is_cacheable(status) == NOT_BY_DEFAULT:
            if headers.expires.is_absent and headers.cache_control.is_absent:
                complain(1177)

    if resp.heuristic_expiration:
        if headers.age > (24 * 60 * 60) and \
                warn.heuristic_expiration not in headers.warning:
            complain(1180)
        if headers.expires.is_present:
            complain(1181)
        elif headers.cache_control.max_age is not None:
            complain(1182)

    if resp.stale:
        if warn.response_is_stale not in headers.warning:
            complain(1186)
        if headers.cache_control.must_revalidate:
            complain(1187)

    for direct1, direct2 in [(cache.public, cache.no_store),
                             (cache.private, cache.public),
                             (cache.private, cache.no_store),
                             (cache.must_revalidate,
                              cache.stale_while_revalidate),
                             (cache.must_revalidate, cache.stale_if_error)]:
        if headers.cache_control[direct1] and headers.cache_control[direct2]:
            complain(1193, directive1=direct1, directive2=direct2)

    for direct1, direct2 in [(cache.max_age, cache.no_cache),
                             (cache.max_age, cache.no_store),
                             (cache.s_maxage, cache.private),
                             (cache.s_maxage, cache.no_cache),
                             (cache.s_maxage, cache.no_store)]:
        if headers.cache_control[direct1] and \
                headers.cache_control[direct2] in [True, []]:
            complain(1238, directive1=direct1, directive2=direct2)

    if headers.vary != u'*' and h.host in headers.vary:
        complain(1235)

    if status == st.unauthorized and headers.www_authenticate.is_absent:
        complain(1194)

    if status == st.proxy_authentication_required and \
            headers.proxy_authenticate.is_absent:
        complain(1195)

    for hdr in [headers.www_authenticate, headers.proxy_authenticate]:
        for challenge in hdr:
            if challenge.item == auth.basic:
                _check_basic_challenge(resp, hdr, challenge)
            if challenge.item == auth.bearer:
                _check_bearer_challenge(resp, hdr, challenge)

    if headers.allow.is_present and headers.accept_patch.is_present and \
            m.PATCH not in headers.allow:
        complain(1217)

    if headers.strict_transport_security.is_okay:
        if hsts.max_age not in headers.strict_transport_security:
            complain(1218)
        if headers.strict_transport_security.max_age == 0 and \
                headers.strict_transport_security.includesubdomains:
            complain(1219)
        for dupe in duplicates(d.item
                               for d in headers.strict_transport_security):
            complain(1220, directive=dupe)

    for patch_type in headers.accept_patch:
        if media_type.is_patch(patch_type.item) == False:
            complain(1227, patch_type=patch_type.item)

    if resp.transformed_by_proxy and headers.via.is_absent:
        complain(1046)

    if status == st.unavailable_for_legal_reasons:
        if not any(rel.blocked_by in link.param.get(u'rel', [])
                   for link in headers.link):
            complain(1243)

    if headers.content_disposition.is_okay:
        params = headers.content_disposition.param
        for name in params.duplicates():
            complain(1247, param=name)

        filename = params.get(u'filename')
        if filename is not None:
            if contains_percent_encodes(filename):
                complain(1248)
            if u'"' in filename or u'\\' in filename:
                # These must have been backslash-escaped.
                complain(1249)
            if not is_ascii(filename):
                complain(1250)

        filename_ext = params.get(u'filename*')
        if filename_ext is not None:
            if filename is None:
                complain(1251)
            elif params.index(u'filename*') < params.index(u'filename'):
                complain(1252)
            if filename_ext.charset != u'UTF-8':
                complain(1255)

    if headers.alt_svc.is_present:
        if version == http2:
            complain(1258)
        if status == st.misdirected_request:
            complain(1260)


def check_response_in_context(resp, req):
    resp.silence(notice_id
                 for (notice_id, in_resp) in req.headers.httpolice_silence
                 if in_resp)

    complain = resp.complain
    method = req.method
    status = resp.status

    if resp.body and resp.headers.content_type.is_absent and \
            (status != st.partial_content or req.headers.if_range.is_absent):
        complain(1041)

    if method == m.CONNECT and status.successful:
        if resp.headers.transfer_encoding.is_present:
            complain(1019)
        if resp.headers.content_length.is_present:
            complain(1024)
        if u'close' in resp.headers.connection:
            complain(1199)
    elif method != m.HEAD and \
            not status.informational and \
            status not in [st.no_content, st.not_modified] and \
            resp.headers.content_length.is_absent and \
            tc.chunked not in resp.headers.transfer_encoding and \
            resp.version == http11:
        complain(1025)
        if u'close' not in resp.headers.connection:
            complain(1047)

    if method == m.HEAD and resp.body:
        complain(1239)

    if req.version == http11 and (not req.headers.host.is_okay or
                                  req.headers.host.total_entries > 1):
        if status.successful or status.redirection:
            complain(1033)

    if resp.transformed_by_proxy and req.is_to_proxy == False:
        complain(1237)

    if req.is_to_proxy and status.successful and resp.headers.via.is_absent:
        # Non-2xx responses may be generated by the proxy itself (e.g. 407).
        complain(1046)

    if status == st.switching_protocols:
        for protocol in resp.headers.upgrade:
            if protocol not in req.headers.upgrade:
                complain(1049)
            elif protocol.item == upgrade.h2c:
                if not req.headers.http2_settings.is_okay:
                    complain(1232)
        if req.version == http10:
            complain(1051)
    elif status.informational and req.version == http10:
        complain(1071)

    if resp.headers.content_location.is_okay and req.effective_uri:
        if req.effective_uri == urljoin(req.effective_uri,
                                        resp.headers.content_location.value):
            if method in [m.GET, m.HEAD] and \
                    status in [st.ok, st.non_authoritative_information,
                               st.no_content, st.partial_content,
                               st.not_modified]:
                complain(1055)
            if method == m.DELETE:
                complain(1060)

    if resp.headers.location.is_okay and req.effective_uri and req.scheme:
        if req.effective_uri == urljoin(req.effective_uri,
                                        resp.headers.location.value):
            if status in [st.multiple_choices, st.temporary_redirect,
                          st.permanent_redirect]:
                complain(1085)
            if status in [st.moved_permanently, st.found, st.see_other] and \
                    method != m.POST:
                complain(1085)

    if method == m.PUT and req.headers.content_range.is_present and \
            status.successful:
        complain(1058)

    if method_info.is_safe(method):
        if status == st.created:
            complain(1072)
        if status == st.accepted:
            complain(1074)
        if status == st.conflict:
            complain(1095)

    if status == st.created and method == m.POST and \
            resp.headers.location.is_absent:
        complain(1073)

    if method != m.HEAD and resp.body == b'':
        if status == st.accepted:
            complain(1284)
        elif status == st.multiple_choices:
            complain(1077)
        elif status == st.see_other:
            complain(1081)
        elif status == st.not_acceptable:
            complain(1092)
        elif status == st.conflict:
            complain(1096)
        elif status == st.precondition_required:
            complain(1201)
        elif status == st.too_many_requests:
            complain(1203)
        elif status == st.unavailable_for_legal_reasons:
            complain(1242)
        elif status.client_error:
            complain(1087)
        elif status == st.http_version_not_supported:
            complain(1106)
        elif status == st.network_authentication_required:
            complain(1204)
        elif status.server_error:
            complain(1104)

    if method == m.OPTIONS and req.target_form is rfc7230.asterisk_form and \
            status in [st.multiple_choices, st.moved_permanently,
                       st.found, st.temporary_redirect, st.permanent_redirect]:
        complain(1086)

    if status == st.not_acceptable:
        if not req.headers.clearly(header.is_proactive_conneg):
            complain(1090)
            # We used to report a separate comment notice (no. 1091)
            # in case the request had some headers we didn't know.
            # But it's unlikely that anyone would use custom conneg headers,
            # and it seems more helpful to report an error in this case
            # (after all, it can be silenced).
        elif req.headers.clearly(header.is_proactive_conneg) == \
                set([h.accept_language]):
            complain(1117)

    if status == st.length_required and req.headers.content_length.is_okay:
        complain(1097)

    if req.body == b'':
        if status == st.payload_too_large:
            complain(1098)

        # Even if the request actually has no body,
        # it makes sense for the server to look at the ``Content-Type``
        # and respond with 415 (Unsupported Media Type) anyway.
        if status == st.unsupported_media_type and \
                req.headers.content_type.is_absent:
            complain(1099)

    if status == st.expectation_failed and req.headers.expect.is_absent:
        complain(1100)

    for protocol in resp.headers.upgrade:
        if protocol in req.headers.upgrade:
            if status == st.upgrade_required:
                complain(1102, protocol=protocol)
            elif status.successful:
                complain(1103, protocol=protocol)
            break

    if status == st.upgrade_required and not resp.headers.upgrade:
        complain(1101)

    if status == st.http_version_not_supported and resp.version and \
            resp.version == req.version:
        complain(1105)

    if status == st.method_not_allowed:
        if method in resp.headers.allow:
            complain(1114)
    elif status.successful:
        if resp.headers.allow.is_present and method not in resp.headers.allow:
            complain(1115)

    if method in [m.GET, m.HEAD] and status.successful:
        if req.headers.if_none_match.is_okay and resp.headers.etag.is_okay:
            if req.headers.if_none_match == u'*':
                # In this case we could ignore the presence of ``ETag``,
                # but then we would need a separate notice
                # that would be pretty useless and too hard to explain.
                complain(1121)
            elif any(tag.weak_equiv(resp.headers.etag.value)
                     for tag in req.headers.if_none_match):
                complain(1121)

        elif req.headers.if_modified_since >= resp.headers.last_modified.value:
            complain(1123)

    if status in [st.not_modified, st.precondition_failed]:
        if method not in [m.GET, m.HEAD] and status == st.not_modified:
            complain(1124)
        elif not req.headers.clearly(header.is_precondition):
            complain(1125)
            # We used to report a separate comment notice (no. 1126)
            # in case the request had some headers we didn't know.
            # But it's unlikely that anyone would use custom preconditions,
            # and it seems more helpful to report an error in this case
            # (after all, it can be silenced).
        elif req.headers.clearly(header.is_precondition) == \
                set([h.if_modified_since]):
            if method not in [m.GET, m.HEAD]:
                complain(1128)
        elif req.headers.clearly(header.is_precondition).issubset(
                set([h.if_match, h.if_none_match,
                     h.if_modified_since, h.if_unmodified_since, h.if_range])):
            if method in [m.CONNECT, m.OPTIONS, m.TRACE]:
                complain(1129)

    if status == st.partial_content:
        if req.headers.range.is_absent:
            complain(1136)
        elif method != m.GET:
            complain(1137)

        if (resp.headers.content_type == media.multipart_byteranges and
                req.headers.range.is_okay and
                req.headers.range.unit == unit.bytes and
                len(req.headers.range.ranges) == 1):
            complain(1144)

        if isinstance(req.headers.if_range.value, EntityTag) and \
                resp.headers.etag.is_okay and \
                not resp.headers.etag.strong_equiv(req.headers.if_range.value):
            complain(1145)

        if req.headers.if_range.is_present:
            for hdr in resp.headers:
                if header.is_representation_metadata(hdr.name) and \
                        hdr.name not in [h.etag, h.content_location]:
                    complain(1146, header=hdr)

    if status == st.range_not_satisfiable:
        if req.headers.range.is_absent:
            complain(1149)
        if req.headers.range.is_okay and \
                req.headers.range.unit == unit.bytes and \
                resp.headers.content_range.is_absent:
            complain(1150)

    if resp.from_cache:
        if method_info.is_cacheable(method) == False:
            complain(1172)
        if resp.headers.age > req.headers.cache_control.max_age:
            complain(1170)
        if req.headers.cache_control.no_cache:
            complain(1173)
        elif req.headers.cache_control.is_absent and \
                u'no-cache' in req.headers.pragma:
            complain(1174)

    if resp.stale and \
            warn.revalidation_failed not in resp.headers.warning and \
            warn.disconnected_operation not in resp.headers.warning and \
            req.headers.cache_control.max_stale is None and \
            req.headers.cache_control.stale_if_error is None and \
            resp.headers.cache_control.stale_if_error is None and \
            resp.headers.cache_control.stale_while_revalidate is None:
        complain(1188)

    if status == st.precondition_required:
        for hdr in req.headers:
            if header.is_precondition(hdr.name):
                complain(1200, header=hdr)
                break

    if method == m.PATCH:
        if status.successful and req.headers.content_type.is_okay and \
                media_type.is_patch(req.headers.content_type.item) == False:
            complain(1214)
        if status == st.unsupported_media_type and \
                resp.headers.accept_patch.is_absent:
            complain(1215)

    if method == m.OPTIONS and m.PATCH in resp.headers.allow and \
            resp.headers.accept_patch.is_absent:
        complain(1216)

    if resp.headers.strict_transport_security.is_present and \
            req.is_tls == False:
        complain(1221)

    if status == st.misdirected_request and method_info.is_cacheable(method) \
            and not resp.headers.cache_control.no_store:
        complain(1283)

    for applied_pref in resp.headers.preference_applied:
        if applied_pref not in req.headers.prefer.without_params:
            complain(1286, name=applied_pref.item,
                     value=(u'' if applied_pref.param is None
                            else u'=%s' % applied_pref.param))

    if resp.headers.preference_applied.is_present and \
            method_info.is_cacheable(method) and \
            not (resp.headers.vary == u'*') and \
            not (resp.headers.vary.is_okay and h.prefer in resp.headers.vary):
            # We could also look for ``Cache-Control: no-store`` etc.,
            # but the meaning of ``Vary`` is not limited to caching,
            # and anyway this is just a mild comment.
        complain(1291)


def _check_basic_challenge(resp, hdr, challenge):
    if isinstance(challenge.param, six.text_type):      # ``token68`` form
        resp.complain(1273, header=hdr)
        return
    if u'realm' not in challenge.param:
        resp.complain(1206, header=hdr)
    for charset in challenge.param.getall(u'charset'):
        if charset.lower() != u'utf-8':
            resp.complain(1208, header=hdr, charset=charset)
    for name in set(challenge.param) - set([u'charset', u'realm']):
        resp.complain(1207, header=hdr, param=name)


def _check_bearer_challenge(resp, hdr, challenge):
    # The ``Bearer`` authentication scheme is actually defined
    # for proxies as well as for servers (RFC 6750 Section 1).
    # Squid even seems to support it:
    # http://wiki.squid-cache.org/Features/BearerAuthentication .
    # However, generalizing these checks to proxies is kind of a pain,
    # so for now we only handle the ``WWW-Authenticate`` series.
    # If this is ever extended to proxies, the notices must be adjusted.
    # Also note that some text in RFC 6750 only applies to servers
    # (where it says "resource server").
    if hdr.name != h.www_authenticate:      # pragma: no cover
        return

    req = resp.request
    request_has_token = None
    if req:
        if req.is_tls == False:
            resp.complain(1263)

        # Did the request contain a bearer token in one of the defined forms?
        request_has_token = (
            (
                req.headers.authorization.is_okay and
                req.headers.authorization.item == auth.bearer
            ) or
            (
                okay(req.url_encoded_data) and
                u'access_token' in req.url_encoded_data
            ) or
            u'access_token' in req.query_params
        )

    params = challenge.param

    if isinstance(params, six.text_type) or not params:
        # ``token68`` form or no parameters at all.
        resp.complain(1264)
        return

    for dupe in params.duplicates():
        if dupe in [u'realm', u'scope', u'error', u'error_description',
                    u'error_uri']:
            resp.complain(1265, param=dupe)

    for param in [u'scope', u'error', u'error_description', u'error_uri']:
        if param in params:
            parser = getattr(rfc6749, param)
            simple_parse(params[param], parser,
                         resp.complain, 1266, param=param, value=params[param])

    if resp.status == st.unauthorized and u'error' not in params and \
            req and req.headers.authorization.is_okay and \
            req.headers.authorization.item == auth.bearer:
        # We don't report this if the token was passed in the URI or body,
        # because the server may not implement those forms at all.
        resp.complain(1267)

    if u'error' in params:
        error_code = params[u'error']
        expected_status = {
            u'invalid_request': st.bad_request,
            u'invalid_token': st.unauthorized,
            u'insufficient_scope': st.forbidden,
        }.get(error_code)
        if expected_status and resp.status != expected_status:
            resp.complain(1268, error_code=error_code,
                          expected_status=expected_status)

    if req and req.headers.authorization.is_absent and not request_has_token:
        for param in [u'error', u'error_description', u'error_uri']:
            if param in params:
                resp.complain(1269, param=param)


def _check_multipart_byteranges(resp):
    if okay(resp.multipart_data):
        for i, part in enumerate(resp.multipart_data.get_payload()):
            if u'Content-Range' not in part:
                resp.complain(1141, part_num=(i + 1))
            if u'Content-Type' not in part:
                resp.complain(1142, part_num=(i + 1))
