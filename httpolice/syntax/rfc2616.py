# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import auto, fill_names, octet_range
from httpolice.syntax.rfc7230 import quoted_string, token


LOALPHA = octet_range(0x61, 0x7A)                                       > auto

value = token | quoted_string                                           > auto


fill_names(globals(), RFC(2616))
