# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import (auto, fill_names, literal, maybe_str, octet_range,
                             pivot, string, string1, string_times)
from httpolice.structure import LanguageTag
from httpolice.syntax.common import ALPHA, DIGIT


singleton = (DIGIT | octet_range(0x41, 0x57) | octet_range(0x59, 0x5A) |
             octet_range(0x61, 0x77) | octet_range(0x79, 0x7A))         > auto
alphanum = ALPHA | DIGIT                                                > auto

irregular = (literal('en-GB-oed') |
             'i-ami'              |
             'i-bnn'              |
             'i-default'          |
             'i-enochian'         |
             'i-hak'              |
             'i-klingon'          |
             'i-lux'              |
             'i-mingo'            |
             'i-navajo'           |
             'i-pwn'              |
             'i-tao'              |
             'i-tay'              |
             'i-tsu'              |
             'sgn-BE-FR'          |
             'sgn-BE-NL'          |
             'sgn-CH-DE')                                               > auto

regular = (literal('art-lojban') |
           'cel-gaulish'         |
           'no-bok'              |
           'no-nyn'              |
           'zh-guoyu'            |
           'zh-hakka'            |
           'zh-min'              |
           'zh-min-nan'          |
           'zh-xiang')                                                  > auto

grandfathered = irregular | regular                                     > pivot
privateuse = 'x' + string1('-' + string_times(1, 8, alphanum))          > pivot

extlang = (string_times(3, 3, ALPHA) +
           string_times(0, 2, '-' + string_times(3, 3, ALPHA)))         > pivot

language = (string_times(2, 3, ALPHA) + maybe_str('-' + extlang) |
            string_times(4, 4, ALPHA) | string_times(5, 8, ALPHA))      > pivot
script = string_times(4, 4, ALPHA)                                      > pivot
region = string_times(2, 2, ALPHA) | string_times(3, 3, DIGIT)          > pivot
variant = (string_times(5, 8, alphanum) |
           (DIGIT + string_times(3, 3, alphanum)))                      > pivot
extension = (singleton + string1('-' + string_times(2, 8, alphanum)))   > pivot

langtag = (language +
           maybe_str('-' + script) +
           maybe_str('-' + region) +
           string('-' + variant) +
           string('-' + extension) +
           maybe_str('-' + privateuse))                                 > pivot

Language_Tag = (LanguageTag << langtag |
                LanguageTag << privateuse |
                LanguageTag << grandfathered)                           > pivot


fill_names(globals(), RFC(5646))
