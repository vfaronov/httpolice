# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import auto, fill_names, many, maybe, pivot, skip, string1
from httpolice.structure import HSTSDirective, Parametrized
from httpolice.syntax.common import DIGIT
from httpolice.syntax.rfc7230 import OWS, quoted_string, token


# This has been slightly adapted to the rules of RFC 7230.
# The ``OWS`` are derived from the "implied ``*LWS``" requirement.

directive_name = HSTSDirective << token                                 > auto
directive_value = token | quoted_string                                 > auto
directive = Parametrized << (
    directive_name * maybe(skip(OWS * '=' * OWS) * directive_value))    > pivot

def _collect_elements(xs):
    return [elem for elem in xs if elem is not None]

Strict_Transport_Security = _collect_elements << (
    maybe(directive) % many(skip(OWS * ';' * OWS) * maybe(directive)))  > pivot

max_age_value = int << string1(DIGIT)                                   > pivot

fill_names(globals(), RFC(6797))
