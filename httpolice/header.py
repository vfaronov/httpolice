# -*- coding: utf-8; -*-

import httpolice.common


class HeaderEntry(object):

    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.annotations = None

    def __repr__(self):
        return u'<HeaderEntry %s>' % self.name


class FieldName(httpolice.common.CaseInsensitive):

    __slots__ = ()


def is_bad_for_trailer(name):
    return known_headers.get_info(name).get('bad_for_trailer')


known_headers = httpolice.common.Known([
    {
        'name': FieldName('Content-Length'),
        'bad_for_trailer': True,
    },
    {
        'name': FieldName('Transfer-Encoding'),
        'bad_for_trailer': True,
    },
])
