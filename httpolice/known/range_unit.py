# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.known.base import KnownDict
from httpolice.structure import RangeUnit


known = KnownDict([
 {'_': RangeUnit(u'bytes'), '_citations': [RFC(7233, section=(2, 1))]},
])
