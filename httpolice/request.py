# -*- coding: utf-8; -*-

import base64
import fnmatch
import itertools
from six.moves.urllib.parse import parse_qs  # pylint: disable=import-error
from six.moves.urllib.parse import urlparse  # pylint: disable=import-error
import string

import six

from httpolice import message
from httpolice.blackboard import derived_property
from httpolice.known import (auth, cache, cache_directive, cc, h, header, m,
                             media_type, method as method_info, pref, product,
                             tc, upgrade)
from httpolice.parse import mark, simple_parse
from httpolice.structure import (EntityTag, Method, MultiDict, Parametrized,
                                 Versioned, http2, http10, http11, okay)
from httpolice.syntax.common import CTL
from httpolice.syntax import rfc7230
from httpolice.syntax.rfc7230 import (absolute_form, asterisk_form,
                                      authority_form, origin_form)
from httpolice.util.data import duplicates
from httpolice.util.text import force_unicode


class Request(message.Message):

    def __init__(self, scheme, method, target, version, header_entries,
                 body, trailer_entries=None, remark=None):
        # pylint: disable=redefined-outer-name
        """
        :param scheme:
            The scheme of the request URI, as a Unicode string
            (usually ``u'http'`` or ``u'https'``),
            or `None` if unknown (this disables some checks).

        :param method:
            The request method, as a Unicode string.

        :param target:
            The request target, as a Unicode string.
            It must be in one of the four forms `defined by RFC 7230`__.
            (For HTTP/2, it can be `reconstructed from pseudo-headers`__.)

            __ https://tools.ietf.org/html/rfc7230#section-5.3
            __ https://tools.ietf.org/html/rfc7540#section-8.1.2.3

        :param version:
            The request's protocol version, as a Unicode string,
            or `None` if unknown (this disables some checks).

            For requests sent over HTTP/1.x connections,
            this should be the HTTP version sent in the `request line`__,
            such as ``u'HTTP/1.0'`` or ``u'HTTP/1.1'``.

            __ https://tools.ietf.org/html/rfc7230#section-3.1.1

            For requests sent over HTTP/2 connections,
            this should be ``u'HTTP/2'``.

        :param header_entries:
            A list of the request's headers (may be empty).
            It must **not** include HTTP/2 `pseudo-headers`__.

            __ https://tools.ietf.org/html/rfc7540#section-8.1.2.1

            Every item of the list must be a ``(name, value)`` pair.

            `name` must be a Unicode string.

            `value` may be a byte string or a Unicode string.
            If it is Unicode, HTTPolice will assume that it has been decoded
            from ISO-8859-1 (the historic encoding of HTTP),
            and will encode it back into ISO-8859-1 before any processing.

        :param body:
            The request's payload body, as a **byte string**,
            or `None` if unknown (this disables some checks).

            If the request has no payload (like a GET request),
            this should be the empty string ``b''``.

            This must be the payload body as `defined by RFC 7230`__:
            **after** removing any ``Transfer-Encoding`` (like ``chunked``),
            but **before** removing any ``Content-Encoding`` (like ``gzip``).

            __ https://tools.ietf.org/html/rfc7230#section-3.3

        :param trailer_entries:
            A list of headers from the request's trailer part
            (as found in `chunked coding`__ or `HTTP/2`__),
            or `None` if there is no trailer part.

            __ https://tools.ietf.org/html/rfc7230#section-4.1.2
            __ https://tools.ietf.org/html/rfc7540#section-8.1

            The format is the same as for `header_entries`.

        :param remark:
            If not `None`, this Unicode string will be shown
            above the request in HTML reports
            (when the appropriate option is enabled).
            For example, it can be used to identify the source of the data:
            ``u'from somefile.dat, offset 1337'``.

        """
        super(Request, self).__init__(version, header_entries, body,
                                      trailer_entries, remark)
        self.scheme = force_unicode(scheme) if scheme is not None else None
        self.method = Method(force_unicode(method))
        self.target = force_unicode(target)

    def __repr__(self):
        return '<Request %s>' % self.method

    @derived_property
    def target_form(self):
        if self.method == m.CONNECT:
            symbol = mark(authority_form)
        elif self.method == m.OPTIONS:
            symbol = (mark(origin_form) | mark(asterisk_form) |
                      mark(absolute_form))
        else:
            symbol = mark(origin_form) | mark(absolute_form)
        r = simple_parse(self.target, symbol,
                         self.complain, 1045, place=u'request target')
        if okay(r):
            (symbol, _) = r
            return symbol
        else:
            return r

    @derived_property
    def effective_uri(self):
        # RFC 7230 section 5.5.
        if self.target_form is absolute_form:
            return self.target

        if self.scheme:
            scheme = self.scheme
        else:           # Let's not annoy the user with wrong guesses.
            return None

        if self.target_form is authority_form:
            authority = self.target
        elif self.headers.host.is_okay:
            authority = self.headers.host.value
        else:
            return None

        if self.target_form in [authority_form, asterisk_form]:
            path_and_query = u''
        elif self.target_form is origin_form:
            path_and_query = self.target
        else:
            return None

        return scheme + u'://' + authority + path_and_query

    @derived_property
    def is_tls(self):
        if self.scheme == u'http':
            return False
        elif self.scheme == u'https':
            return True
        return None

    @derived_property
    def is_to_proxy(self):
        # In HTTP/1.x, the absolute form of the request target
        # is reserved for requests to proxies,
        # but this is no longer true in HTTP/2
        # (which has its own equivalent of the absolute form
        # with the ``:authority`` pseudo-header).
        if self.version in [http10, http11]:
            if self.target_form is absolute_form:
                self.complain(1236)
                return True
            else:
                return False
        return None

    @derived_property
    def query_params(self):
        # `parse_qs` returns an empty dictionary on garbage,
        # so this property should be understood as "salvageable query params."
        if not okay(self.effective_uri):
            return {}
        return parse_qs(urlparse(self.effective_uri).query)

    @derived_property
    def has_body(self):
        # Even though our input data does not distinguish
        # between "no body" and "empty body",
        # we can reconstruct this distinction later
        # according to the rules of RFC 7230 Section 3.3.
        if self.body:
            return True
        if self.version in [http10, http11]:
            return (self.headers.content_length.is_present or
                    self.headers.transfer_encoding.is_present)
        return None


def check_request(req):
    """Apply all checks to the request `req`."""
    complain = req.complain
    method = req.method
    version = req.version
    headers = req.headers
    body = req.body

    req.silence(notice_id
                for (notice_id, in_resp) in headers.httpolice_silence
                if not in_resp)

    message.check_message(req)

    # Check the syntax of request method and target.
    simple_parse(method, rfc7230.method,
                 complain, 1292, place=u'request method')
    _ = req.target_form

    if method != method.upper() and method.upper() in m:
        complain(1295, uppercase=Method(method.upper()))

    if body and headers.content_type.is_absent:
        complain(1041)

    if (version in [http10, http11] and method_info.defines_body(method) and
            headers.content_length.is_absent and
            headers.transfer_encoding.is_absent):
        complain(1021)

    if (method_info.defines_body(method) == False) and (body == b'') and \
            headers.content_length.is_present:
        complain(1022)

    if tc.chunked in headers.te:
        complain(1028)

    if version == http2:
        if headers.te and headers.te != [u'trailers']:
            complain(1244, header=headers.te)
    else:
        if headers.te and u'TE' not in headers.connection:
            complain(1029)

    if version == http11 and headers.host.is_absent:
        complain(1031)
    if headers.host.is_present and req.header_entries[0].name != h.host:
        complain(1032)

    for hdr in headers:
        if header.is_for_request(hdr.name) == False:
            complain(1063, header=hdr)
        elif header.is_representation_metadata(hdr.name) and \
                req.has_body == False:
            complain(1053, header=hdr)

    if body:
        if method == m.GET:
            complain(1056)
        elif method == m.HEAD:
            complain(1057)
        elif method == m.DELETE:
            complain(1059)
        elif method == m.CONNECT:
            complain(1061)

    if method == m.OPTIONS and body and headers.content_type.is_absent:
        complain(1062)

    if headers.expect == u'100-continue' and req.has_body == False:
        complain(1066)

    if headers.max_forwards.is_present and method not in [m.OPTIONS, m.TRACE]:
        complain(1067)

    if headers.referer.is_okay:
        if req.is_tls == False:
            parsed = urlparse(headers.referer.value)
            if parsed.scheme == u'https':
                complain(1068)

    if headers.user_agent.is_absent:
        complain(1070)
    elif headers.user_agent.is_okay:
        products = [p for p in headers.user_agent if isinstance(p, Versioned)]
        if products and all(product.is_library(p.item) for p in products):
            complain(1093, library=products[0])

    for x in headers.accept_encoding:
        if x.item in [cc.x_gzip, cc.x_compress] and x.param is not None:
            complain(1116, coding=x.item)

    if headers.if_match.is_okay and headers.if_match != u'*':
        if any(tag.weak for tag in headers.if_match):
            complain(1120)

    if method == m.HEAD:
        for hdr in headers:
            if header.is_precondition(hdr.name):
                complain(1131, header=hdr)

    if method in [m.CONNECT, m.OPTIONS, m.TRACE]:
        for hdr in headers:
            if hdr.name in [h.if_modified_since, h.if_unmodified_since,
                            h.if_match, h.if_none_match, h.if_range]:
                complain(1130, header=hdr)
    elif method not in [m.GET, m.HEAD]:
        if headers.if_modified_since.is_present:
            complain(1122)

    if headers.range.is_present and method != m.GET:
        complain(1132)

    if headers.if_range.is_present and headers.range.is_absent:
        complain(1134)

    if isinstance(headers.if_range.value, EntityTag) and headers.if_range.weak:
        complain(1135)

    for direct in headers.cache_control:
        if cache_directive.is_for_request(direct.item) == False:
            complain(1152, directive=direct.item)
        if direct == cache.no_cache and direct.param is not None:
            complain(1159, directive=direct.item)

    if headers.cache_control.no_cache and u'no-cache' not in headers.pragma:
        complain(1161)

    for warning in headers.warning:
        if 100 <= warning.code <= 199:
            complain(1165, code=warning.code)

    if method_info.is_cacheable(method) == False:
        for direct in headers.cache_control:
            if direct.item in [cache.max_age, cache.max_stale, cache.min_fresh,
                               cache.no_cache, cache.no_store,
                               cache.only_if_cached]:
                complain(1171, directive=direct)

    for direct1, direct2 in [(cache.max_stale, cache.min_fresh),
                             (cache.stale_if_error, cache.min_fresh),
                             (cache.max_stale, cache.no_cache),
                             (cache.max_age, cache.no_cache)]:
        if headers.cache_control[direct1] and headers.cache_control[direct2]:
            complain(1193, directive1=direct1, directive2=direct2)

    for hdr in [headers.authorization, headers.proxy_authorization]:
        if hdr.is_okay:
            scheme, credentials = hdr.value
            if scheme == auth.basic:
                _check_basic_auth(req, hdr, credentials)
            elif scheme == auth.bearer:
                _check_bearer_auth(req, hdr, credentials)
            elif not credentials:
                complain(1274, header=hdr)

    if method == m.PATCH and headers.content_type.is_okay:
        if media_type.is_patch(headers.content_type.item) == False:
            complain(1213)

    for protocol in headers.upgrade:
        if protocol.item == upgrade.h2c:
            if req.is_tls:
                complain(1233)
            if headers.http2_settings.is_absent:
                complain(1231)

    if headers.http2_settings and u'HTTP2-Settings' not in headers.connection:
        complain(1230)

    if headers.http2_settings.is_okay:
        if not _is_urlsafe_base64(headers.http2_settings.value):
            complain(1234)

    if u'access_token' in req.query_params:
        complain(1270)
        if req.is_tls == False:
            complain(1271, where=req.target)
        if not headers.cache_control.no_store:
            complain(1272)

    if okay(req.url_encoded_data) and u'access_token' in req.url_encoded_data:
        if req.is_tls == False:
            complain(1271, where=req.displayable_body)

    for hdr in [headers.accept, headers.accept_charset,
                headers.accept_encoding, headers.accept_language]:
        for (wildcard, value) in _accept_subsumptions(hdr):
            complain(1276, header=hdr, wildcard=wildcard, value=value)
            # No need to report more than one subsumption per header.
            break

    for dup_pref in duplicates(name for ((name, _), _) in headers.prefer):
        complain(1285, name=dup_pref)

    if headers.prefer.respond_async and method_info.is_safe(method):
        complain(1287)

    if headers.prefer.return_ == u'minimal' and method == m.GET:
        complain(1288)

    if (pref.return_, u'minimal') in headers.prefer.without_params and \
       (pref.return_, u'representation') in headers.prefer.without_params:
        complain(1289)

    if (pref.handling, u'strict') in headers.prefer.without_params and \
       (pref.handling, u'lenient') in headers.prefer.without_params:
        complain(1290)


def _check_basic_auth(req, hdr, credentials):
    if isinstance(credentials, six.text_type):   # ``token68`` form
        try:
            credentials = base64.b64decode(credentials)
        except Exception as e:
            req.complain(1210, header=hdr, error=e)
        else:
            # RFC 7617 section 2 requires that,
            # whatever the encoding of the credentials,
            # it must be ASCII-compatible, so we don't need to know it.
            if b':' not in credentials:
                req.complain(1211, header=hdr)
            for c in six.iterbytes(credentials):
                if CTL.match(six.int2byte(c)):
                    req.complain(1212, header=hdr, char=hex(c))
    else:
        req.complain(1209, header=hdr)


def _check_bearer_auth(req, hdr, credentials):
    if req.is_tls == False:
        req.complain(1261, header=hdr)
    if not isinstance(credentials, six.text_type):      # not ``token68`` form
        req.complain(1262, header=hdr)


def _accept_subsumptions(items):
    """Find items in an Accept-like header that subsume one another."""
    normalized = []
    for (item, q) in items:
        if isinstance(item, Parametrized):          # The ``Accept`` header.
            item = item.item
        if q is None:
            q = 1.0
        elif isinstance(q, MultiDict):              # The ``Accept`` header.
            q = q.get(u'q', 1.0)
        normalized.append((item, q))

    for ((item1, q1), (item2, q2)) in itertools.permutations(normalized, 2):
        if (item1 == u'*' or item1.endswith(u'/*')) and \
                fnmatch.fnmatch(item2, item1) and \
                not fnmatch.fnmatch(item1, item2) and \
                q1 == q2:
            yield (item1, item2)


def _is_urlsafe_base64(s):
    alphabet = string.ascii_letters + string.digits + '-_'
    return all(c in alphabet for c in s)
