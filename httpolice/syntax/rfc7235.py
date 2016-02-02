# -*- coding: utf-8; -*-

from httpolice.parse import (
    argwrap,
    char_class,
    decode,
    eof,
    function,
    join,
    literal,
    lookahead,
    maybe,
    rfc,
    string,
    string1,
    wrap,
)
from httpolice.structure import AuthScheme, CaseInsensitive, Parametrized
from httpolice.syntax.common import ALPHA, DIGIT, sp
from httpolice.syntax.rfc7230 import bws, comma_list, ows, quoted_string, token


auth_scheme = wrap(AuthScheme, token)   // rfc(7235, u'auth-scheme')

def _parse_auth_param(state):
    k, v = (token + ~(bws + '=' + bws) + (token | quoted_string)).parse(state)
    k = CaseInsensitive(k)
    # Rely on the fact that `token` returns `unicode`
    # whereas `quoted_string` returns `str`
    # (because the text inside a quoted string may be non-ASCII).
    if k == u'realm' and isinstance(v, unicode):
        state.complain(1196)
    return k, v

auth_param = function(_parse_auth_param)

token68 = decode(join(string1(char_class(ALPHA + DIGIT + '-._~+/')) +
                      string('=')))   // rfc(7235, u'token68')

def _parse_auth_params(state):
    r = comma_list(auth_param).parse(state)

    # TODO: this evil hack is needed because of the ambiguity
    # between the final comma of ``#auth_param``
    # and the intermediate comma of ``1#challenge``
    # (see the note in RFC 7235 section 4.1).
    if state.data[state.pos - 1] == ',':
        state.pos -= 1

    # Normalize "no parameters" to `None`.
    return r or None

challenge = credentials = argwrap(
    Parametrized,
    auth_scheme +
    maybe(~string1(sp) +
          ((token68 + ~lookahead(ows + (eof | literal(',')))) |
           function(_parse_auth_params))))
