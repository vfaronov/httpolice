# -*- coding: utf-8; -*-

from httpolice.common import LanguageTag
from httpolice.parse import char_class, decode_into, rfc, string1
from httpolice.syntax.common import ALPHA, DIGIT


language_tag = decode_into(                                 # TODO
    LanguageTag,
    string1(char_class(ALPHA + DIGIT + '-'))) \
    // rfc(5646, u'Language-Tag')
