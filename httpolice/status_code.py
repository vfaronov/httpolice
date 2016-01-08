# -*- coding: utf-8; -*-

from httpolice import common


class StatusCode(int):

    def __resp__(self):
        return 'StatusCode(%d)' % self

    informational = property(lambda self: 100 <= self < 199)
    successful = property(lambda self: 200 <= self < 299)
    redirection = property(lambda self: 300 <= self < 399)
    client_error = property(lambda self: 400 <= self < 499)
    server_error = property(lambda self: 500 <= self < 599)


def reason(code):
    return known_codes.get_info(code).get('name')


class KnownStatusCodes(common.Known):

    @classmethod
    def _key_for(cls, item):
        return item['code']


known_codes = KnownStatusCodes([
    {
        'code': StatusCode(101), 'name': u'Switching Protocols',
    },
    {
        'code': StatusCode(204), 'name': u'No Content',
    },
    {
        'code': StatusCode(304), 'name': u'Not Modified',
    }
])
