# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import (
    auto,
    can_complain,
    fill_names,
    maybe,
    pivot,
    skip,
    string,
    string1,
)
from httpolice.structure import (
    AuthScheme,
    CaseInsensitive,
    Parametrized,
    Quoted,
)
from httpolice.syntax.common import ALPHA, DIGIT, SP
from httpolice.syntax.rfc7230 import (
    BWS,
    comma_list,
    comma_list1,
    quoted_string,
    token,
)


auth_scheme = AuthScheme << token                                       > pivot
token68 = (string1(ALPHA | DIGIT | '-' | '.' | '_' | '~' | '+' | '/') +
           string('='))                                                 > pivot

@can_complain
def _check_realm(complain, k, v):
    if isinstance(v, Quoted):
        v = v.item
    elif k == u'realm':
        complain(1196)
    return (k, v)

auth_param = _check_realm << ((CaseInsensitive << token) *
                              skip(BWS * '=' * BWS) *
                              (token | Quoted << quoted_string))        > pivot

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
