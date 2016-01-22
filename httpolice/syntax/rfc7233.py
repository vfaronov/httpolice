# -*- coding: utf-8; -*-

from httpolice.common import RangeSpecifier, RangeUnit
from httpolice.parse import (
    ParseError,
    argwrap,
    ci,
    decode,
    eof,
    function,
    literal,
    lookahead,
    maybe,
    string1,
    subst,
    wrap,
)
from httpolice.syntax.common import integer, vchar
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
    r = RangeUnit(token.parse(state))
    if r == RangeUnit(u'bytes'):
        raise ParseError()
    return r

other_range_unit = function(_parse_other_range_unit)
other_range_set = decode(string1(vchar))
other_ranges_specifier = argwrap(
    RangeSpecifier,
    other_range_unit + ~literal('=') + other_range_set)

range = other_ranges_specifier | byte_ranges_specifier
