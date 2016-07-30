# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.known.base import KnownDict
from httpolice.structure import TransferCoding


known = KnownDict(TransferCoding, [
 {'_': TransferCoding(u'chunked'),
  '_citations': [RFC(7230, section=(4, 1))]},
 {'_': TransferCoding(u'compress'),
  '_citations': [RFC(7230, section=(4, 2, 1))]},
 {'_': TransferCoding(u'deflate'),
  '_citations': [RFC(7230, section=(4, 2, 2))]},
 {'_': TransferCoding(u'gzip'),
  '_citations': [RFC(7230, section=(4, 2, 3))]},
 {'_': TransferCoding(u'identity'),
  # https://www.rfc-editor.org/errata_search.php?eid=408
  '_no_sync': True},
 {'_': TransferCoding(u'x-compress'),
  '_citations': [RFC(7230, section=(4, 2, 1))]},
 {'_': TransferCoding(u'x-gzip'),
  '_citations': [RFC(7230, section=(4, 2, 2))]}
])
