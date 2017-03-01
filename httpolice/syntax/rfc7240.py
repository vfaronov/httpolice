# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import fill_names, many, maybe, named, pivot, skip
from httpolice.structure import CaseInsensitive, Parametrized, Preference
from httpolice.syntax.rfc7230 import OWS, comma_list1, token
from httpolice.syntax.rfc7231 import parameter


def _normalize_empty_value(x):
    # RFC 7240 Section 2: "Empty or zero-length values on both
    # the preference token and within parameters are equivalent
    # to no value being specified at all."
    (name, value) = x if isinstance(x, tuple) else (x, None)
    return Parametrized(name, None if value == u'' else value)

def preference_parameter(head=False):
    # The head (first) ``preference-parameter`` of a ``preference``
    # contains the actual preference name, which we want to annotate.
    name_cls = Preference if head else CaseInsensitive
    return (
        _normalize_empty_value << (parameter(name_cls=name_cls) |
                                   name_cls << token)
    ) > named(u'preference-parameter', RFC(7240, errata=4439), is_pivot=True)

preference = Parametrized << (
    preference_parameter(head=True) *
    many(skip(OWS * ';') * maybe(skip(OWS) * preference_parameter()))
) > named(u'preference', RFC(7240, errata=4439), is_pivot=True)

Prefer = comma_list1(preference)                                        > pivot

Preference_Applied = comma_list1(preference_parameter(head=True))       > pivot


fill_names(globals(), RFC(7240))
