# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import auto, fill_names, string_times
from httpolice.syntax.common import ALPHA, DIGIT


restricted_name_first = ALPHA | DIGIT                                   > auto
restricted_name_chars = (ALPHA | DIGIT | '!' | '#' |
                         '$' | '&' | '-' | '^' | '_' |
                         '.' | '+')                                     > auto
restricted_name = (restricted_name_first +
                   string_times(0, 126, restricted_name_chars))         > auto

type_name = restricted_name                                             > auto
subtype_name = restricted_name                                          > auto


fill_names(globals(), RFC(6838))
