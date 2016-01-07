# -*- coding: utf-8; -*-

from httpolice import common


class TransferCoding(common.CaseInsensitive):

    __slots__ = ()


known_codings = common.Known([
    {'name': TransferCoding('chunked')},
])
