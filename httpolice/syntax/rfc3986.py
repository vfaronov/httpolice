# -*- coding: utf-8; -*-

from httpolice.parse import char_class, join, string
from httpolice.syntax.common import (ALPHA, DIGIT, HEXDIG)


pct_encoded = join('%' + char_class(HEXDIG) + char_class(HEXDIG))
sub_delims = char_class("!$&'()*+,;=")
unreserved = char_class(ALPHA + DIGIT + "-._~")
pchar = unreserved | pct_encoded | sub_delims | char_class(':@')
segment = string(pchar)
query = string(pchar | char_class('/?'))
