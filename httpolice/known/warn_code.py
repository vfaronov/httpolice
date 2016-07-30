# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.known.base import KnownDict
from httpolice.structure import WarnCode


known = KnownDict(WarnCode, [
 {'_': WarnCode(110),
  '_citations': [RFC(7234, section=(5, 5, 1))],
  '_title': u'Response is Stale'},
 {'_': WarnCode(111),
  '_citations': [RFC(7234, section=(5, 5, 2))],
  '_title': u'Revalidation Failed'},
 {'_': WarnCode(112),
  '_citations': [RFC(7234, section=(5, 5, 3))],
  '_title': u'Disconnected Operation'},
 {'_': WarnCode(113),
  '_citations': [RFC(7234, section=(5, 5, 4))],
  '_title': u'Heuristic Expiration'},
 {'_': WarnCode(199),
  '_citations': [RFC(7234, section=(5, 5, 5))],
  '_title': u'Miscellaneous Warning'},
 {'_': WarnCode(214),
  '_citations': [RFC(7234, section=(5, 5, 6))],
  '_title': u'Transformation Applied'},
 {'_': WarnCode(299),
  '_citations': [RFC(7234, section=(5, 5, 7))],
  '_title': u'Miscellaneous Persistent Warning'},
 ],
 name_from_title=True
)
