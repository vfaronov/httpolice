# -*- coding: utf-8; -*-

from httpolice.common import CacheDirective, Parametrized
from httpolice.parse import argwrap, literal, maybe, wrap
from httpolice.syntax.rfc7230 import quoted_string, token


cache_directive = argwrap(
    Parametrized,
    wrap(CacheDirective, token) +
    maybe(~literal('=') + (token | quoted_string)))
