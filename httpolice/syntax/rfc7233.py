# -*- coding: utf-8; -*-

from httpolice.common import ContentRange, RangeSpecifier, RangeUnit
from httpolice.parse import (
    ParseError,
    argwrap,
    ci,
    decode,
    eof,
    function,
    group,
    literal,
    lookahead,
    maybe,
    string,
    string1,
    subst,
    wrap,
)
from httpolice.syntax.common import char, integer, vchar
from httpolice.syntax.rfc7230 import comma_list1, token


acceptable_ranges = (
    subst([], ci('none') + ~lookahead(eof)) |
    comma_list1(wrap(RangeUnit, token)))

bytes_unit = wrap(RangeUnit, ci('bytes'))

def _parse_byte_range_spec(state):
    first, last = (integer + ~literal('-') + maybe(integer)).parse(state)
    if (last is not None) and (first > last):
        state.complain(1133)
    return first, last

byte_range_spec = function(_parse_byte_range_spec)
suffix_byte_range_spec = wrap(
    lambda x: (None, x),
    ~literal('-') + integer)
byte_range_set = comma_list1(byte_range_spec | suffix_byte_range_spec)
byte_ranges_specifier = argwrap(
    RangeSpecifier,
    bytes_unit + ~literal('=') + byte_range_set)

def _parse_other_range_unit(state):
    r = wrap(RangeUnit, token).parse(state)
    if r == RangeUnit(u'bytes'):
        raise ParseError()
    return r

other_range_unit = function(_parse_other_range_unit)
other_range_set = decode(string1(vchar))
other_ranges_specifier = argwrap(
    RangeSpecifier,
    other_range_unit + ~literal('=') + other_range_set)

range = other_ranges_specifier | byte_ranges_specifier

byte_range = integer + ~literal('-') + integer
byte_range_resp = (
    group(byte_range) + ~literal('/') + (integer | subst(None, '*')))
unsatisfied_range = subst(None, '*/') + integer

def _parse_byte_content_range(state):
    inner = bytes_unit + ~literal(' ') + (byte_range_resp | unsatisfied_range)
    r = ContentRange(*inner.parse(state))
    bounds, complete = r.range
    if bounds is not None:
        first, last = bounds
        if (last < first) or ((complete is not None) and (complete <= last)):
            state.complain(1148)
    return r

byte_content_range = function(_parse_byte_content_range)

other_range_resp = string(char)
other_content_range = argwrap(
    ContentRange,
    other_range_unit + ~literal(' ') + other_range_resp)

content_range = other_content_range | byte_content_range
