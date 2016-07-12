# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.parse import (auto, fill_names, many, octet, octet_range, pivot,
                             skip, string1)
from httpolice.syntax.common import SP
from httpolice.syntax.rfc3986 import URI_reference


NQSCHAR = (octet_range(0x20, 0x21) | octet_range(0x23, 0x5B) |
           octet_range(0x5D, 0x7E))                                     > auto
NQCHAR = (octet(0x21) | octet_range(0x23, 0x5B) |
          octet_range(0x5D, 0x7E))                                      > auto

scope_token = string1(NQCHAR)                                           > pivot
scope = scope_token % many(skip(SP) * scope_token)                      > pivot

error = string1(NQSCHAR)                                                > pivot
error_description = string1(NQSCHAR)                                    > pivot
error_uri = URI_reference                                               > pivot


fill_names(globals(), RFC(6749))
