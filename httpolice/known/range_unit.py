# -*- coding: utf-8; -*-

from httpolice.common import RFC, RangeUnit
from httpolice.known.base import KnownDict


known = KnownDict([
 {'_': RangeUnit(u'bytes'), '_citations': [RFC(7233, section=(2, 1))]},
])
