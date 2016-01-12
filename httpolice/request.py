# -*- coding: utf-8; -*-

from httpolice import message, parse
from httpolice.common import http11
from httpolice.known import h, header, m, method, tc
from httpolice.syntax import rfc7230


class Request(message.Message):

    def __repr__(self):
        return '<Request %s>' % self.method

    def __init__(self, method_, target, version_, header_entries,
                 body=None, trailer_entries=None, raw=None):
        super(Request, self).__init__(version_, header_entries,
                                      body, trailer_entries, raw)
        self.method = method_
        self.target = target
        self._parse_target()

    def _parse_target(self):
        # The ``<request-target>`` story is complicated by the fact
        # that there is syntactic overlap between the 4 possible forms.
        # For instance, ``example.com:80`` can be parsed as ``<absolute-URI>``
        # with a ``<scheme>`` of ``example.com``
        # and a ``<path-rootless>`` of ``80``.
        # Similarly, ``*`` can be parsed as ``<authority>``.
        # So we just compute and remember 4 separate flags.
        for form_name, parser in [('origin', rfc7230.origin_form),
                                  ('absolute', rfc7230.absolute_form),
                                  ('authority', rfc7230.authority_form),
                                  ('asterisk', rfc7230.asterisk_form)]:
            try:
                (parser + parse.eof).parse(parse.State(self.target))
            except parse.ParseError:
                result = False
            else:
                result = True
            setattr(self, 'is_%s_form' % form_name, result)

        self.is_to_proxy = self.is_absolute_form and self.method != m.CONNECT


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
        if header.is_representation_metadata(hdr.name) and \
                req.body is None:
            req.complain(1053, header=hdr)
