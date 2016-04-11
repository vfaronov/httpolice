# -*- coding: utf-8; -*-

import base64

try:
    from urllib.parse import urlparse
except ImportError:                             # Python 2
    from urlparse import urlparse

import six

from httpolice import message, parse
from httpolice.blackboard import memoized_property
from httpolice.known import (
    auth,
    cache,
    cache_directive,
    cc,
    h,
    header,
    m,
    media_type,
    method,
    product,
    tc,
)
from httpolice.structure import EntityTag, Versioned, http11, okay
from httpolice.syntax import rfc7230
from httpolice.syntax.common import CTL


class RequestView(message.MessageView):

    def __repr__(self):
        return '<RequestView %s>' % self.method

    scheme = property(lambda self: self.inner.scheme)
    method = property(lambda self: self.inner.method)
    target = property(lambda self: self.inner.target)

    def _target_parses_as(self, parser):
        try:
            parse.Stream(self.target.encode('ascii', 'replace')). \
                parse(parser, to_eof=True)
        except parse.ParseError:
            return False
        else:
            return True

    @memoized_property
    def is_origin_form(self):
        return self._target_parses_as(rfc7230.origin_form)

    @memoized_property
    def is_asterisk_form(self):
        return self._target_parses_as(rfc7230.asterisk_form)

    @memoized_property
    def is_authority_form(self):
        return (
            self._target_parses_as(rfc7230.authority_form) and
            # ``*`` can be parsed as an ``<authority>``.
            not self.is_asterisk_form)

    @memoized_property
    def is_absolute_form(self):
        return (
            self._target_parses_as(rfc7230.absolute_form) and
            # ``example.com:80`` can be parsed as an ``<absolute-URI>``
            # with a ``<scheme>`` of ``example.com``
            # and a ``<path-rootless>`` of ``80``.
            not self.is_authority_form)

    @memoized_property
    def effective_uri(self):
        # RFC 7230 section 5.5.
        if self.is_absolute_form:
            return self.target
        if self.scheme:
            scheme = self.scheme
        else:           # Let's not annoy the user with wrong guesses.
            return None
        if self.is_authority_form:
            authority = self.target
        elif self.headers.host.is_okay:
            authority = self.headers.host.value
        else:
            return None
        if self.is_authority_form or self.is_asterisk_form:
            path_and_query = u''
        elif self.is_origin_form:
            path_and_query = self.target
        else:
            return None
        return scheme + u'://' + authority + path_and_query


def check_request(req):
    message.check_message(req)

    if req.body and req.headers.content_type.is_absent:
        req.complain(1041)

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

    if req.version == http11 and req.headers.host.is_absent:
        req.complain(1031)
    if req.headers.host.is_present and req.header_entries[0].name != h.host:
        req.complain(1032)

    if req.method == m.CONNECT:
        if not req.is_authority_form:
            req.complain(1043)
    elif req.method == m.OPTIONS:
        if not req.is_origin_form and not req.is_asterisk_form \
                and not req.is_absolute_form:
            req.complain(1044)
    else:
        if not req.is_origin_form and not req.is_absolute_form:
            req.complain(1045)

    for hdr in req.headers:
        if header.is_for_request(hdr.name) == False:
            req.complain(1063, header=hdr)
        elif header.is_representation_metadata(hdr.name) and not req.body:
            req.complain(1053, header=hdr)

    if req.body:
        if req.method == m.GET:
            req.complain(1056)
        elif req.method == m.HEAD:
            req.complain(1057)
        elif req.method == m.DELETE:
            req.complain(1059)
        elif req.method == m.CONNECT:
            req.complain(1061)

    if req.method == m.OPTIONS and req.body and \
            req.headers.content_type.is_absent:
        req.complain(1062)

    if req.headers.expect.is_present:
        if req.headers.expect == b'100-continue':
            if not req.body:
                req.complain(1066)
        else:
            req.complain(1065)

    if req.headers.max_forwards.is_present and \
            req.method not in [m.OPTIONS, m.TRACE]:
        req.complain(1067)

    if req.headers.referer.is_okay:
        if req.scheme == u'http':
            parsed = urlparse(req.headers.referer.value)
            if parsed.scheme == u'https':
                req.complain(1068)

    if req.headers.user_agent.is_absent:
        req.complain(1070)
    elif req.headers.user_agent.is_okay:
        products = [p for p in req.headers.user_agent.value
                    if isinstance(p, Versioned)]
        if products and all(product.is_library(p.item) for p in products):
            req.complain(1093, library=products[0])

    for x in req.headers.accept_encoding.okay:
        if x.item in [cc.x_gzip, cc.x_compress] and x.param is not None:
            req.complain(1116, coding=x.item)

    if req.headers.if_match.is_okay and req.headers.if_match != u'*':
        if any(tag.weak for tag in req.headers.if_match.value):
            req.complain(1120)

    if req.method == m.HEAD:
        for hdr in req.headers:
            if header.is_precondition(hdr.name):
                req.complain(1131, header=hdr)

    if req.method in [m.CONNECT, m.OPTIONS, m.TRACE]:
        for hdr in req.headers:
            if hdr.name in [h.if_modified_since, h.if_unmodified_since,
                            h.if_match, h.if_none_match, h.if_range]:
                req.complain(1130, header=hdr)
    elif req.method not in [m.GET, m.HEAD]:
        if req.headers.if_modified_since.is_present:
            req.complain(1122)

    if req.headers.range.is_present and req.method != m.GET:
        req.complain(1132)

    if req.headers.if_range.is_present and req.headers.range.is_absent:
        req.complain(1134)

    if isinstance(req.headers.if_range.value, EntityTag) and \
            req.headers.if_range.value.weak:
        req.complain(1135)

    for d in req.headers.cache_control.okay:
        if cache_directive.is_for_request(d.item) == False:
            req.complain(1152, directive=d.item)
        if d == cache.no_cache and d.param is not None:
            req.complain(1159, directive=d.item)

    if req.headers.cache_control.no_cache and \
            u'no-cache' not in req.headers.pragma:
        req.complain(1161)

    for warning in req.headers.warning.okay:
        if 100 <= warning.code < 200:
            req.complain(1165, code=warning.code)

    if method.is_cacheable(req.method) == False:
        for direct in req.headers.cache_control.okay:
            if direct.item in [cache.max_age, cache.max_stale, cache.min_fresh,
                               cache.no_cache, cache.no_store,
                               cache.only_if_cached]:
                req.complain(1171, directive=direct)

    for direct1, direct2 in [(cache.max_stale, cache.min_fresh),
                             (cache.max_stale, cache.no_cache),
                             (cache.max_age, cache.no_cache)]:
        if req.headers.cache_control[direct1] and \
                req.headers.cache_control[direct2]:
            req.complain(1193, directive1=direct1, directive2=direct2)

    for hdr in [req.headers.authorization, req.headers.proxy_authorization]:
        if hdr.is_okay:
            scheme, credentials = hdr.value
            if scheme == auth.basic:
                if isinstance(credentials, six.text_type):   # ``token68`` form
                    try:
                        credentials = base64.b64decode(credentials)
                    except Exception as e:
                        req.complain(1210, header=hdr, error=e)
                    else:
                        # RFC 7617 section 2 requires that,
                        # whatever the encoding of the credentials,
                        # it must be ASCII-compatible,
                        # so we don't need to know it.
                        if b':' not in credentials:
                            req.complain(1211, header=hdr)
                        for c in six.iterbytes(credentials):
                            if CTL.match(six.int2byte(c)):
                                req.complain(1212, header=hdr, char=hex(c))
                else:
                    req.complain(1209, header=hdr)

    if req.method == m.PATCH and req.headers.content_type.is_okay:
        if media_type.is_patch(req.headers.content_type.value.item) == False:
            req.complain(1213)

    if any(proto.item == u'h2' for proto in req.headers.upgrade.okay):
        req.complain(1228)
