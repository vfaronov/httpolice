# -*- coding: utf-8; -*-

from httpolice import common
from httpolice.common import Unparseable


class TransferCoding(common.CaseInsensitive):

    __slots__ = ()


def decode(body, coding):
    return Unparseable


known_codings = common.Known([
    {'name': TransferCoding('chunked')},
])
