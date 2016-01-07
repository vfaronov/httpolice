# -*- coding: utf-8; -*-

from collections import namedtuple


class _Unparseable(object):

    __slots__ = ()

    def __repr__(self):
        return 'Unparseable'

Unparseable = _Unparseable()


class ProtocolString(unicode):

    __slots__ = ()

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self)


class CaseInsensitive(ProtocolString):

    __slots__ = ()

    def __eq__(self, other):
        return unicode.lower(self) == unicode.lower(other)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(unicode.lower(self))


Parametrized = namedtuple('Parametrized', ('item', 'params'))
Parameter = namedtuple('Parameter', ('name', 'value'))


class Comment(ProtocolString):

    __slots__ = ()


class OriginForm(ProtocolString):

    __slots__ = ()


class AsteriskForm(ProtocolString):

    __slots__ = ()


class Known(object):

    def __init__(self, items):
        self._by_key = dict((self._key_for(item), item) for item in items)
        self._by_name = dict((self._name_for(item), item) for item in items)

    def __getattr__(self, name):
        if name in self._by_name:
            return self._key_for(self._by_name[name])
        else:
            raise AttributeError(name)

    def __getitem__(self, key):
        return self._by_key[key]

    def get_info(self, key):
        return self._by_key.get(key, {})

    def __iter__(self):
        return iter(self._by_key)

    def __contains__(self, key):
        return key in self._by_key

    @classmethod
    def _key_for(cls, item):
        return item['name']

    @classmethod
    def _name_for(cls, item):
        return item['name'].replace(u'-', u' ').replace(u' ', u'_').lower()
