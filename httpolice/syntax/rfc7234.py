# -*- coding: utf-8; -*-

from httpolice.common import CacheDirective, Parametrized
from httpolice.parse import (
    ParseError,
    argwrap,
    ci,
    function,
    literal,
    maybe,
    rfc,
    wrap,
)
from httpolice.syntax.rfc7230 import quoted_string, token


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
