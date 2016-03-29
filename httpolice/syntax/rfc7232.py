# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import (
    auto,
    can_complain,
    decode,
    fill_names,
    literal,
    maybe,
    octet,
    octet_range,
    pivot,
    string,
    subst,
)
from httpolice.structure import EntityTag
from httpolice.syntax.common import DQUOTE
from httpolice.syntax.rfc7230 import comma_list1, obs_text
from httpolice.syntax.rfc7231 import HTTP_date


weak = subst(True) << octet(0x57) * octet(0x2F)                         > auto
etagc = octet(0x21) | octet_range(0x23, 0x7E) | obs_text                > auto

@can_complain
def _no_backslashes(complain, s):
    if '\\' in s:
        complain(1119)
    return s

opaque_tag = _no_backslashes << DQUOTE + string(etagc) + DQUOTE         > auto
entity_tag = EntityTag << maybe(weak, False) * opaque_tag               > pivot

ETag = entity_tag                                                       > pivot
Last_Modified = HTTP_date                                               > pivot

If_Match = decode << literal('*') | comma_list1(entity_tag)             > pivot
If_None_Match = decode << literal('*') | comma_list1(entity_tag)        > pivot
If_Modified_Since = HTTP_date                                           > pivot
If_Unmodified_Since = HTTP_date                                         > pivot

fill_names(globals(), RFC(7232))
