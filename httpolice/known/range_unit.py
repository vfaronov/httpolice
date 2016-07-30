# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.known.base import KnownDict
from httpolice.structure import RangeUnit


known = KnownDict(RangeUnit, [
 {'_': RangeUnit(u'bytes'), '_citations': [RFC(7233, section=(2, 1))]},
 {'_': RangeUnit(u'none'), '_no_sync': True},
])
