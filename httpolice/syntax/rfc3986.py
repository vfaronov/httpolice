# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import (auto, empty, fill_names, literal, maybe_str,
                             octet_range, pivot, string, string1, string_times,
                             subst)
from httpolice.syntax.common import ALPHA, DIGIT, HEXDIG


pct_encoded = '%' + HEXDIG + HEXDIG                                     > auto
sub_delims = (literal('!') | '$' | '&' | "'" | '(' | ')' | '*' | '+' |
              ',' | ';' | '=')                                          > auto
unreserved = ALPHA | DIGIT | '-' | '.' | '_' | '~'                      > auto
pchar = unreserved | sub_delims | ':' | '@' | pct_encoded               > auto

segment = string(pchar)                                                 > auto
segment_nz = string1(pchar)                                             > auto
segment_nz_nc = string1(unreserved | sub_delims | '@' | pct_encoded)    > auto

scheme = ALPHA + string(ALPHA | DIGIT | '+' | '-' | '.')                > pivot
userinfo = string(unreserved | sub_delims | ':' | pct_encoded)          > pivot
dec_octet = (DIGIT |
             octet_range(0x31, 0x39) + DIGIT |
             '1' + DIGIT + DIGIT |
             '2' + octet_range(0x30, 0x34) + DIGIT |
             '25' + octet_range(0x30, 0x35))                            > auto
IPv4address = (dec_octet + '.' + dec_octet + '.' +
               dec_octet + '.' + dec_octet)                             > pivot
h16 = string_times(1, 4, HEXDIG)                                        > auto
ls32 = (h16 + ':' + h16) | IPv4address                                  > auto
IPv6address = (
    string_times(6, 6, h16 + ':') + ls32 |
    '::' + string_times(5, 5, h16 + ':') + ls32 |
    maybe_str(h16) + '::' + string_times(4, 4, h16 + ':') + ls32 |
    maybe_str(string_times(0, 1, h16 + ':') + h16) +
        '::' + string_times(3, 3, h16 + ':') + ls32 |
    maybe_str(string_times(0, 2, h16 + ':') + h16) +
        '::' + string_times(2, 2, h16 + ':') + ls32 |
    maybe_str(string_times(0, 3, h16 + ':') + h16) + '::' + h16 + ':' + ls32 |
    maybe_str(string_times(0, 4, h16 + ':') + h16) + '::' + ls32 |
    maybe_str(string_times(0, 5, h16 + ':') + h16) + '::' + h16 |
    maybe_str(string_times(0, 6, h16 + ':') + h16) + '::'
    )                                                                   > pivot

IPvFuture = ('v' + string1(HEXDIG) + '.' +
             string1(unreserved | sub_delims | ':'))                    > pivot

# As updated by RFC 6874
ZoneID = string1(unreserved | pct_encoded)                              > pivot
IPv6addrz = IPv6address + '%25' + ZoneID                                > pivot
IP_literal = '[' + (IPv6address | IPv6addrz | IPvFuture) + ']'          > pivot

reg_name = string(unreserved | sub_delims | pct_encoded)                > pivot
host = IP_literal | IPv4address | reg_name                              > pivot
port = string(DIGIT)                                                    > pivot
authority = maybe_str(userinfo + '@') + host + maybe_str(':' + port)    > pivot

path_abempty = string('/' + segment)                                    > auto
path_absolute = '/' + maybe_str(segment_nz + string('/' + segment))     > auto
path_noscheme = segment_nz_nc + string('/' + segment)                   > auto
path_rootless = segment_nz + string('/' + segment)                      > auto
path_empty = subst(u'') << empty                                        > auto

hier_part = ('//' + authority + path_abempty |
             path_absolute | path_rootless | path_empty)                > pivot

query = string(pchar | '/' | '?')                                       > pivot
fragment = string(pchar | '/' | '?')                                    > pivot

absolute_URI = scheme + ':' + hier_part + maybe_str('?' + query)        > pivot

relative_part = ('//' + authority + path_abempty |
                 path_absolute | path_noscheme | path_empty)            > pivot

URI = (scheme + ':' + hier_part +
       maybe_str('?' + query) + maybe_str('#' + fragment))              > pivot

relative_ref = (relative_part +
                maybe_str('?' + query) + maybe_str('#' + fragment))     > pivot

URI_reference = URI | relative_ref                                      > pivot


fill_names(globals(), RFC(3986))
