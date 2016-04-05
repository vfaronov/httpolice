# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import auto, fill_names, octet, octet_range


ALPHA = octet_range(0x41, 0x5A) | octet_range(0x61, 0x7A)               > auto
CHAR = octet_range(0x01, 0x7F)                                          > auto
CTL = octet_range(0x00, 0x1F) | octet(0x7F)                             > auto
CR = octet(0x0D)                                                        > auto
DIGIT = octet_range(0x30, 0x39)                                         > auto
DQUOTE = octet(0x22)                                                    > auto
HEXDIG = DIGIT | 'A' | 'B' | 'C' | 'D' | 'E' | 'F'                      > auto
HTAB = octet(0x09)                                                      > auto
LF = octet(0x0A)                                                        > auto
SP = octet(0x20)                                                        > auto
VCHAR = octet_range(0x21, 0x7E)                                         > auto

CRLF = CR + LF                                                          > auto

fill_names(globals(), RFC(5234))
