# -*- coding: utf-8; -*-

from httpolice.parse import (
    argwrap,
    many,
    maybe,
    wrap,
)
from httpolice.structure import HSTSDirective, Parametrized
from httpolice.syntax.rfc7230 import ows, quoted_string, token


# This has been slightly adapted to the rules of RFC 7230.
# The ``<OWS>`` are derived from the "linear ``*LWS``" requirement.

directive_name = wrap(HSTSDirective, token)
directive_value = token | quoted_string
directive = argwrap(
    Parametrized,
    directive_name + maybe(~(ows + '=' + ows) + directive_value))

strict_transport_security = argwrap(
    lambda x, xs: [elem for elem in [x] + xs if elem is not None],
    maybe(directive) +
    many(~(ows + ';' + ows) + maybe(directive)))
