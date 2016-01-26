# -*- coding: utf-8; -*-

import urlparse

from httpolice import message, parse
from httpolice.common import EntityTag, Versioned, http11, okay
from httpolice.known import (
    cache,
    cache_directive,
    cc,
    h,
    header,
    m,
    method,
    product,
    tc,
)
from httpolice.syntax import rfc7230


class Request(message.Message):

    def __repr__(self):
        return '<Request %s>' % self.method

    def __init__(self, method_, target, version_, header_entries,
                 body=None, trailer_entries=None, scheme=None, raw=None):
        super(Request, self).__init__(version_, header_entries,
                                      body, trailer_entries, raw)
        self.method = method_
        self.target = target
        self._parse_target()
        self.scheme = scheme
        self.effective_uri = self._build_effective_uri()

    def _parse_target(self):
        def _parses_as(parser):
            try:
                (parser + parse.eof).parse(parse.State(self.target))
            except parse.ParseError:
                return False
            else:
                return True
        self.is_origin_form = _parses_as(rfc7230.origin_form)
        self.is_asterisk_form = _parses_as(rfc7230.asterisk_form)
        self.is_authority_form = (
            _parses_as(rfc7230.authority_form)
            # ``*`` can be parsed as an ``<authority>``.
            and not self.is_asterisk_form)
        self.is_absolute_form = (
            _parses_as(rfc7230.absolute_form)
            # ``example.com:80`` can be parsed as an ``<absolute-URI>``
            # with a ``<scheme>`` of ``example.com``
            # and a ``<path-rootless>`` of ``80``.
            and not self.is_authority_form)

    def _build_effective_uri(self):
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
            path_and_query = ''
        elif self.is_origin_form:
            path_and_query = self.target
        else:
            return None
        return scheme + '://' + authority + path_and_query


def check_request(req):
    message.check_message(req)
    message.check_payload_body(req)

    if okay(req.body) and req.body and req.headers.content_type.is_absent:
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
        elif header.is_representation_metadata(hdr.name) and \
                req.body is None:
            req.complain(1053, header=hdr)

    if okay(req.body) and req.body:
        if req.method == m.GET:
            req.complain(1056)
        elif req.method == m.HEAD:
            req.complain(1057)
        elif req.method == m.DELETE:
            req.complain(1059)
        elif req.method == m.CONNECT:
            req.complain(1061)

    if req.method == m.OPTIONS and \
            okay(req.body) and req.body and req.headers.content_type.is_absent:
        req.complain(1062)

    if req.headers.expect.is_present:
        if req.headers.expect == '100-continue':
            if req.body is None:
                req.complain(1066)
        else:
            req.complain(1065)

    if req.headers.max_forwards.is_present and \
            req.method not in [m.OPTIONS, m.TRACE]:
        req.complain(1067)

    if req.headers.referer.is_okay:
        if req.scheme == 'http' and \
                urlparse.urlparse(req.headers.referer.value).scheme == 'https':
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
