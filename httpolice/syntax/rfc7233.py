# -*- coding: utf-8; -*-

from httpolice.common import RangeUnit
from httpolice.parse import ci, eof, lookahead, subst, wrap
from httpolice.syntax.rfc7230 import comma_list1, token


acceptable_ranges = (
    subst([], ci('none') + ~lookahead(eof)) |
    comma_list1(wrap(RangeUnit, token)))
