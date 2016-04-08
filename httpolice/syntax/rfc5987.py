# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import (
    auto,
    fill_names,
    literal,
    maybe,
    named,
    pivot,
    string,
    string1,
    string_excluding,
    skip,
)
from httpolice.syntax.common import ALPHA, DIGIT, HEXDIG
from httpolice.syntax.rfc5646 import Language_Tag as language


attr_char = (ALPHA | DIGIT |
             '!' | '#' | '$' | '&' | '+' | '-' | '.' |
             '^' | '_' | '`' | '|' | '~')                               > auto

def parmname__excluding(exclude):
    return (string_excluding(attr_char, [''] + exclude)
            > named(u'parmname', RFC(5987), is_pivot=True))

parmname = parmname__excluding([])

mime_charsetc = (ALPHA | DIGIT |
                 '!' | '#' | '$' | '%' | '&' | '+' | '-' | '^' | '_' | '`' |
                 '{' | '}' | '~')                                       > auto
mime_charset = string1(mime_charsetc)                                   > auto
charset = literal('UTF-8') | 'ISO-8859-1' | mime_charset                > pivot

pct_encoded = '%' + HEXDIG + HEXDIG                                     > auto
value_chars = string(pct_encoded | attr_char)                           > auto

ext_value = (charset * skip("'") *
             maybe(language) * skip("'") *
             value_chars)                                               > pivot


fill_names(globals(), RFC(5987))
