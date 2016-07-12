# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import (auto, can_complain, fill_names, mark, maybe,
                             pivot, skip, string, string1)
from httpolice.structure import (AuthScheme, CaseInsensitive, MultiDict,
                                 Parametrized)
from httpolice.syntax.common import ALPHA, DIGIT, SP
from httpolice.syntax.rfc7230 import (BWS, comma_list, comma_list1,
                                      quoted_string, token)


auth_scheme = AuthScheme << token                                       > pivot
token68 = (string1(ALPHA | DIGIT | '-' | '.' | '_' | '~' | '+' | '/') +
           string('='))                                                 > pivot

@can_complain
def _check_realm(complain, k, v):
    (symbol, v) = v
    if k == u'realm' and symbol is not quoted_string:
        complain(1196)
    return (k, v)

auth_param = _check_realm << ((CaseInsensitive << token) *
                              skip(BWS * '=' * BWS) *
                              (mark(token) | mark(quoted_string)))      > pivot

challenge = Parametrized << (
    auth_scheme *
    maybe(skip(string1(SP)) * (token68 |
                               MultiDict << comma_list(auth_param)),
          default=MultiDict()))                                         > auto

WWW_Authenticate = comma_list1(challenge)                               > pivot
Proxy_Authenticate = comma_list1(challenge)                             > pivot

credentials = Parametrized << (
    auth_scheme *
    maybe(skip(string1(SP)) * (token68 |
                               MultiDict << comma_list(auth_param)),
          default=MultiDict()))                                         > auto

Authorization = credentials                                             > pivot
Proxy_Authorization = credentials                                       > pivot

fill_names(globals(), RFC(7235))
