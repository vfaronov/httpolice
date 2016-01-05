# -*- coding: utf-8; -*-

class _Unparseable(object):

    __slots__ = ()

    def __repr__(self):
        return 'Unparseable'

Unparseable = _Unparseable()


class ProtocolString(unicode):

    __slots__ = ()

    def __repr__(self):
        return u'%s(%r)' % (self.__class__.__name__, unicode(self))


class CaseInsensitive(ProtocolString):

    __slots__ = ()

    def __eq__(self, other):
        return unicode(self).lower() == unicode(other).lower()

    def __hash__(self):
        return hash(unicode(self).lower())


class Comment(ProtocolString):

    __slots__ = ()


class OriginForm(ProtocolString):

    __slots__ = ()


class AsteriskForm(ProtocolString):

    __slots__ = ()


class Known(object):

    key_field = 'name'
    display_field = 'name'

    def __init__(self, items):
        self.index = dict((self._translate(item[self.key_field]), item)
                          for item in items)

    def __getattr__(self, key):
        return self.index[key][self.display_field]

    def __getitem__(self, pre_key):
        return self.index[self._translate(pre_key)]

    @staticmethod
    def _translate(key):
        return key.replace(u'-', u' ').replace(u' ', u'_').lower()
