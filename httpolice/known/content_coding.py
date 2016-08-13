# -*- coding: utf-8; -*-

from httpolice.citation import RFC, Citation
from httpolice.known.base import KnownDict
from httpolice.structure import ContentCoding


known = KnownDict(ContentCoding, [
 {'_': ContentCoding(u'br'), '_citations': [RFC(7932)]},
 {'_': ContentCoding(u'compress'),
  '_citations': [RFC(7230, section=(4, 2, 1))]},
 {'_': ContentCoding(u'deflate'),
  '_citations': [RFC(7230, section=(4, 2, 2))]},
 {'_': ContentCoding(u'exi'),
  '_citations': [Citation(u'W3C Recommendation: '
                          u'Efficient XML Interchange (EXI) Format',
                          u'http://www.w3.org/TR/exi/')]},
 {'_': ContentCoding(u'gzip'),
  '_citations': [RFC(7230, section=(4, 2, 3))]},
 {'_': ContentCoding(u'identity'),
  '_citations': [RFC(7231, section=(5, 3, 4))]},
 {'_': ContentCoding(u'pack200-gzip'),
  '_citations': [Citation(u'JSR 200: Network Transfer Format for Java',
                          u'http://www.jcp.org/en/jsr/detail?id=200')]},
 {'_': ContentCoding(u'x-compress'),
  '_citations': [RFC(7230, section=(4, 2, 1))]},
 {'_': ContentCoding(u'x-gzip'), '_citations': [RFC(7230, section=(4, 2, 3))]}
])
