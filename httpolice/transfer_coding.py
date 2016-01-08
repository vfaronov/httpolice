# -*- coding: utf-8; -*-

from httpolice import common
from httpolice.common import RFC


class TransferCoding(common.CaseInsensitive):

    __slots__ = ()


known_codings = common.KnownDict([
 {'_': TransferCoding(u'chunked'), '_citations': [RFC(7230)]},
 {'_': TransferCoding(u'compress'), '_citations': [RFC(7230)]},
 {'_': TransferCoding(u'deflate'), '_citations': [RFC(7230)]},
 {'_': TransferCoding(u'gzip'), '_citations': [RFC(7230)]},
 {'_': TransferCoding(u'identity'), '_citations': [RFC(2616)]},
 {'_': TransferCoding(u'x-compress'), '_citations': [RFC(7230)]},
 {'_': TransferCoding(u'x-gzip'), '_citations': [RFC(7230)]}
])
