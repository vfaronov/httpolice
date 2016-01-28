# -*- coding: utf-8; -*-

from httpolice.common import (
    CacheDirective,
    Parametrized,
    WarnCode,
    WarningValue,
)
from httpolice.parse import (
    ParseError,
    argwrap,
    ci,
    decode,
    function,
    join,
    literal,
    maybe,
    rfc,
    stringx,
    wrap,
)
from httpolice.syntax import rfc3986
from httpolice.syntax.common import digit, dquote, sp
from httpolice.syntax.rfc7230 import quoted_string, pseudonym, token
from httpolice.syntax.rfc7231 import http_date


cache_directive = argwrap(
    Parametrized,
    wrap(CacheDirective, token) +
    maybe(~literal('=') + (token | quoted_string)))

def _parse_extension_pragma(state):
    inner = token + maybe(~literal('=') + (token | quoted_string))
    k, v = inner.parse(state)
    if k.lower() == u'no-cache':
        raise ParseError()
    state.complain(1160, pragma=k)
    return k, v

extension_pragma = function(_parse_extension_pragma) \
    // rfc(7234, u'extension-pragma')

pragma_directive = extension_pragma | ci('no-cache')

warn_code = wrap(WarnCode, stringx(3, 3, digit))   // rfc(7234, u'warn-code')
warn_agent = (
    decode(join(rfc3986.host + maybe(join(':' + rfc3986.port), ''))) |
    pseudonym)
warn_text = quoted_string
warn_date = ~dquote + http_date + ~dquote
warning_value = argwrap(
    WarningValue,
    warn_code + ~sp + warn_agent + ~sp + warn_text + maybe(~sp + warn_date))
