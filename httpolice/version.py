# -*- coding: utf-8; -*-

import httpolice.common


class HTTPVersion(httpolice.common.ProtocolString):

    __slots__ = ()


http10 = HTTPVersion('HTTP/1.0')
http11 = HTTPVersion('HTTP/1.1')
