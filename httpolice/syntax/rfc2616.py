# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import auto, fill_names, octet_range


LOALPHA = octet_range(0x61, 0x7A)                                       > auto


fill_names(globals(), RFC(2616))
