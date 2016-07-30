# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.known.base import KnownDict
from httpolice.structure import AuthScheme


known = KnownDict(AuthScheme, [
 {'_': AuthScheme(u'Basic'), '_citations': [RFC(7617)]},
 {'_': AuthScheme(u'Bearer'), '_citations': [RFC(6750)]},
 {'_': AuthScheme(u'Digest'), '_citations': [RFC(7616)]},
 {'_': AuthScheme(u'HOBA'), '_citations': [RFC(7486, section=(3,))]},
 {'_': AuthScheme(u'Negotiate'), '_citations': [RFC(4559, section=(3,))]},
 {'_': AuthScheme(u'OAuth'), '_citations': [RFC(5849, section=(3, 5, 1))]},
 {'_': AuthScheme(u'SCRAM-SHA-1'), '_citations': [RFC(7804)]},
 {'_': AuthScheme(u'SCRAM-SHA-256'), '_citations': [RFC(7804)]}
])
