# -*- coding: utf-8; -*-

from httpolice.parse import char_class, decode_into, join, rfc, string, stringx
from httpolice.structure import LanguageTag
from httpolice.syntax.common import ALPHA, DIGIT


# FIXME: using the much simpler RFC 3066 syntax
# until I work out the parsers story.

primary_subtag = stringx(1, 8, char_class(ALPHA))
subtag = stringx(1, 8, char_class(ALPHA + DIGIT))
language_tag = decode_into(
    LanguageTag,
    join(primary_subtag + string(join('-' + subtag)))) \
    // rfc(5646, u'Language-Tag')
