# -*- coding: utf-8; -*-

from httpolice import common


class HTTPVersion(common.ProtocolString):

    __slots__ = ()


http10 = HTTPVersion(u'HTTP/1.0')
http11 = HTTPVersion(u'HTTP/1.1')
