# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import (
    auto,
    can_complain,
    decode,
    fill_names,
    maybe,
    pivot,
    skip,
    string,
    string1,
)
from httpolice.structure import AuthScheme, CaseInsensitive, Parametrized
from httpolice.syntax.common import ALPHA, DIGIT, SP
from httpolice.syntax.rfc7230 import (
    BWS,
    comma_list,
    comma_list1,
    quoted_string,
    token,
)


auth_scheme = AuthScheme << token                                       > pivot
token68 = decode << (
    string1(ALPHA | DIGIT | '-' | '.' | '_' | '~' | '+' | '/') +
    string('='))                                                        > pivot

@can_complain
def _check_realm(complain, k, v):
    k = CaseInsensitive(k)
    # Rely on the fact that `token` returns `unicode`
    # whereas `quoted_string` returns `str`
    # (because the text inside a quoted string may be non-ASCII).
    if k == u'realm' and isinstance(v, unicode):
        complain(1196)
    return (k, v)

auth_param = _check_realm << (token * skip(BWS * '=' * BWS) *
                              (token | quoted_string))                  > pivot

def _empty_to_none(r):
    return r or None

challenge = Parametrized << (
    auth_scheme *
    maybe(skip(string1(SP)) *
          (token68 | _empty_to_none << comma_list(auth_param))))        > auto

WWW_Authenticate = comma_list1(challenge)                               > pivot
Proxy_Authenticate = comma_list1(challenge)                             > pivot

credentials = Parametrized << (
    auth_scheme *
    maybe(skip(string1(SP)) *
          (token68 | _empty_to_none << comma_list(auth_param))))        > auto

Authorization = credentials                                             > pivot
Proxy_Authorization = credentials                                       > pivot

fill_names(globals(), RFC(7235))
