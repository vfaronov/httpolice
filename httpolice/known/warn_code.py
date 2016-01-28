# -*- coding: utf-8; -*-

from httpolice.common import RFC, WarnCode
from httpolice.known.base import KnownDict


known = KnownDict([
 {'_': WarnCode(110),
  '_citations': [RFC(7234, section=(5, 5, 1))],
  '_title': 'Response is Stale'},
 {'_': WarnCode(111),
  '_citations': [RFC(7234, section=(5, 5, 2))],
  '_title': 'Revalidation Failed'},
 {'_': WarnCode(112),
  '_citations': [RFC(7234, section=(5, 5, 3))],
  '_title': 'Disconnected Operation'},
 {'_': WarnCode(113),
  '_citations': [RFC(7234, section=(5, 5, 4))],
  '_title': 'Heuristic Expiration'},
 {'_': WarnCode(199),
  '_citations': [RFC(7234, section=(5, 5, 5))],
  '_title': 'Miscellaneous Warning'},
 {'_': WarnCode(214),
  '_citations': [RFC(7234, section=(5, 5, 6))],
  '_title': 'Transformation Applied'},
 {'_': WarnCode(299),
  '_citations': [RFC(7234, section=(5, 5, 7))],
  '_title': 'Miscellaneous Persistent Warning'},
 ],
 name_from_title=True
)
