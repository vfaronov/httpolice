# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import auto, fill_names, pivot, string, string_times
from httpolice.structure import CaseInsensitive
from httpolice.syntax.common import ALPHA, DIGIT


alphanum = ALPHA | DIGIT                                                > auto
language_range = CaseInsensitive << (
    string_times(1, 8, ALPHA) + string('-' + string_times(1, 8, alphanum)) |
    '*')                                                                > pivot


fill_names(globals(), RFC(4647))
