# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import (auto, can_complain, fill_names, literal, maybe,
                             pivot, skip, string, string1, subst)
from httpolice.structure import ContentRange, RangeSpecifier, RangeUnit
from httpolice.syntax.common import CHAR, DIGIT, SP, VCHAR
from httpolice.syntax.rfc7230 import comma_list1, token__excluding
from httpolice.syntax.rfc7231 import HTTP_date
from httpolice.syntax.rfc7232 import entity_tag


bytes_unit = RangeUnit << literal('bytes')                              > auto
other_range_unit = RangeUnit << token__excluding(['bytes'])             > auto
range_unit = bytes_unit | other_range_unit                              > pivot
acceptable_ranges = (
    subst([]) << literal('none') |
    comma_list1(range_unit))                                            > pivot
Accept_Ranges = acceptable_ranges                                       > pivot

@can_complain
def _well_formed1(complain, first, last):
    if (last is not None) and (first > last):
        complain(1133)
    return (first, last)

first_byte_pos = int << string1(DIGIT)                                  > auto
last_byte_pos = int << string1(DIGIT)                                   > auto
byte_range_spec = _well_formed1 << (first_byte_pos * skip('-') *
                                    maybe(last_byte_pos))               > pivot

suffix_length = int << string1(DIGIT)                                   > auto
suffix_byte_range_spec = \
    (lambda x: (None, x)) << skip('-') * suffix_length                  > pivot

byte_range_set = comma_list1(byte_range_spec | suffix_byte_range_spec)  > auto
byte_ranges_specifier = RangeSpecifier << (
    bytes_unit * skip('=') * byte_range_set)                            > pivot

other_range_set = string1(VCHAR)                                        > auto
other_ranges_specifier = RangeSpecifier << (
    other_range_unit * skip('=') * other_range_set)                     > pivot

Range = byte_ranges_specifier | other_ranges_specifier                  > pivot

byte_range = first_byte_pos * skip('-') * last_byte_pos                 > auto
complete_length = int << string1(DIGIT)                                 > auto
byte_range_resp = (
    byte_range * skip('/') *
    (complete_length | subst(None) << literal('*')))                    > pivot

unsatisfied_range = (
    (subst(None) << literal('*/')) * complete_length)                   > pivot

@can_complain
def _well_formed2(complain, r):
    bounds, complete = r.range
    if bounds is not None:
        first, last = bounds
        if (last < first) or ((complete is not None) and (complete <= last)):
            complain(1148)
    return r

byte_content_range = _well_formed2 << (ContentRange << (
    bytes_unit * skip(SP) * (byte_range_resp | unsatisfied_range)))     > pivot

other_range_resp = string(CHAR)                                         > pivot
other_content_range = ContentRange << (
    other_range_unit * skip(SP) * other_range_resp)                     > pivot

Content_Range = byte_content_range | other_content_range                > pivot

If_Range = entity_tag | HTTP_date                                       > pivot

fill_names(globals(), RFC(7233))
