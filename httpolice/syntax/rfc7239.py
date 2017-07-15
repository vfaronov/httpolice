# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import (fill_names, many, maybe, pivot, skip, string1,
                             string_times)
from httpolice.structure import ForwardedParam
from httpolice.syntax.common import ALPHA, DIGIT
from httpolice.syntax.rfc3986 import IPv4address, IPv6address
from httpolice.syntax.rfc7230 import comma_list1, quoted_string, token


def _remove_empty(xs):
    return [x for x in xs if x is not None]


obfnode = '_' + string1(ALPHA | DIGIT | '.' | '_' | '-')                > pivot
nodename = (IPv4address |
            skip('[') * IPv6address * skip(']') |
            'unknown' | obfnode)                                        > pivot

port = int << string_times(1, 5, DIGIT)                                 > pivot
obfport = '_' + string1(ALPHA | DIGIT | '.' | '_' | '-')                > pivot
node_port = port | obfport                                              > pivot

node = nodename * maybe(skip(':') * node_port)                          > pivot

value = token | quoted_string                                           > pivot
forwarded_pair = (ForwardedParam << token) * skip('=') * value          > pivot

forwarded_element = _remove_empty << (
    maybe(forwarded_pair) % many(skip(';') * maybe(forwarded_pair)))    > pivot

Forwarded = comma_list1(forwarded_element)                              > pivot


fill_names(globals(), RFC(7239))
