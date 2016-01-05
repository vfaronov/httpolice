# -*- coding: utf-8; -*-

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
