# -*- coding: utf-8; -*-

import httpolice.common


class HeaderEntry(object):

    def __init__(self, name, value, position=None):
        self.name = name
        self.value = value
        self.position = position
        self.annotations = None

    def __repr__(self):
        return u'<HeaderEntry %r %r>' % (self.position, unicode(self.name))

    @property
    def is_from_trailer(self):
        return None if self.position is None else (self.position < 0)


class FieldName(httpolice.common.CaseInsensitive):

    __slots__ = ()


class KnownHeaders(httpolice.common.Known):

    pass


known_headers = KnownHeaders([
    {'name': FieldName('Content-Length')},
    {'name': FieldName('Transfer-Encoding')},
])
