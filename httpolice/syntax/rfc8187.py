# -*- coding: utf-8; -*-

from httpolice.util.moves import unquote_to_bytes as pct_decode

from httpolice.citation import RFC
from httpolice.parse import (auto, can_complain, fill_names, maybe, pivot,
                             skip, string, string1)
from httpolice.structure import CaseInsensitive, ExtValue
from httpolice.syntax.common import ALPHA, DIGIT, HEXDIG
from httpolice.syntax.rfc5646 import Language_Tag as language
from httpolice.util.text import force_bytes


attr_char = (ALPHA | DIGIT |
             '!' | '#' | '$' | '&' | '+' | '-' | '.' |
             '^' | '_' | '`' | '|' | '~')                               > auto
parmname = string(attr_char)                                            > pivot

# We don't need to special-case "UTF-8", simplify.
mime_charsetc = (ALPHA | DIGIT |
                 '!' | '#' | '$' | '%' | '&' | '+' | '-' | '^' | '_' | '`' |
                 '{' | '}' | '~')                                       > auto
mime_charset = string1(mime_charsetc)                                   > auto
charset = CaseInsensitive << mime_charset                               > pivot

pct_encoded = '%' + HEXDIG + HEXDIG                                     > auto
value_chars = pct_decode << (
    force_bytes << string(pct_encoded | attr_char))                     > auto

@can_complain
def _check_ext_value(complain, val):
    if val.charset == u'UTF-8':
        try:
            val.value_bytes.decode(val.charset)
        except UnicodeError as e:
            complain(1254, charset=val.charset, error=e)
    else:
        complain(1253, charset=val.charset)
    return val

ext_value = _check_ext_value << (
    ExtValue << (charset * skip("'") *
                 maybe(language) * skip("'") *
                 value_chars))                                          > pivot


fill_names(globals(), RFC(8187))
