# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.known.base import KnownDict
from httpolice.structure import UpgradeToken


known = KnownDict(UpgradeToken, [
 {'_': UpgradeToken(u'HTTP'),
  '_citations': [RFC(7230, section=(2, 6))],
  '_title': u'Hypertext Transfer Protocol'},
 {'_': UpgradeToken(u'TLS'),
  '_citations': [RFC(2817)],
  '_title': u'Transport Layer Security'},
 {'_': UpgradeToken(u'WebSocket'),
  '_citations': [RFC(6455)],
  '_title': u'The Web Socket Protocol'},
 {'_': UpgradeToken(u'h2c'),
  '_citations': [RFC(7540, section=(3, 2))],
  '_title': u'Hypertext Transfer Protocol version 2 (HTTP/2)'}
])
