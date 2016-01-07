# -*- coding: utf-8; -*-

from httpolice import common


class Method(common.ProtocolString):

    __slots__ = ()


class KnownMethods(common.Known):

    @classmethod
    def _name_for(cls, item):
        return item['name']


known_methods = KnownMethods([
    {
        'name': Method('HEAD'),
    },
    {
        'name': Method('POST'),
    },
    {
        'name': Method('CONNECT'),
    },
])
