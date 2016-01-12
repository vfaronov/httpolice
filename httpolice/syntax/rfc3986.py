# -*- coding: utf-8; -*-

from httpolice.parse import (
    char_class,
    join,
    literal,
    maybe,
    rfc,
    string,
    string1,
    stringx,
)
from httpolice.syntax.common import (
    ALPHA,
    DIGIT,
    HEXDIG,
    digit,
    hexdig,
)


pct_encoded = join('%' + char_class(HEXDIG) + char_class(HEXDIG))
sub_delims = char_class("!$&'()*+,;=")
unreserved = char_class(ALPHA + DIGIT + "-._~")
pchar = unreserved | pct_encoded | sub_delims | char_class(':@')

segment = string(pchar)
segment_nz = string1(pchar)
segment_nz_nc = string1(unreserved | pct_encoded | sub_delims | '@')

scheme = join(char_class(ALPHA) + string(char_class(ALPHA + DIGIT + '+-.'))) \
    // rfc(3986, u'scheme')
userinfo = string(unreserved | pct_encoded | sub_delims | ':') \
    // rfc(3986, u'userinfo')
dec_octet = (
    digit |
    join(char_class('123456789') + digit) |
    join('1' + stringx(2, 2, digit)) |
    join('2' + char_class('01234') + digit) |
    join('25' + char_class('012345')))
ipv4address = join(
    dec_octet + '.' + dec_octet + '.' + dec_octet + '.' + dec_octet) \
    // rfc(3986, u'IPv4address')
ipv6address = string1(char_class(HEXDIG + ':.'))     # TODO
ipvfuture = join(
    'v' + string1(hexdig) + '.' + string1(unreserved | sub_delims | ':'))
ip_literal = join('[' + (ipv6address | ipvfuture) + ']') \
    // rfc(3986, u'IP-literal')
# FIXME: I had to temporarily remove ``<sub-delims>`` from ``<reg-name>``
# because it was messing up my naive parser in comma lists (e.g. in ``Via``).
reg_name = string(unreserved | pct_encoded)   // rfc(3986, u'reg-name')
host = ip_literal | ipv4address | reg_name
port = string(digit)   // rfc(3986, u'port')
authority = join(maybe(join(userinfo + '@'), '') +
                 host + maybe(join(':' + port), ''))

path_abempty = string(join('/' + segment))   // rfc(3986, u'path-abempty')
path_absolute = join(
    '/' +
    maybe(join(segment_nz + string(join('/' + segment))), '')) \
    // rfc(3986, u'path-absolute')
path_noscheme = join(segment_nz_nc + string(join('/' + segment))) \
    // rfc(3986, u'path-noscheme')
path_rootless = join(segment_nz + string(join('/' + segment))) \
    // rfc(3986, u'path-rootless')
path_empty = literal('')   // rfc(3986, u'path-empty')

hier_part = (join('//' + authority + path_abempty) |
             path_absolute | path_rootless | path_empty)

query = string(pchar | char_class('/?'))

absolute_uri = join(scheme + ':' + hier_part + maybe(join('?' + query), ''))

relative_part = (join('//' + authority + path_abempty) |
                 path_absolute | path_noscheme | path_empty)
