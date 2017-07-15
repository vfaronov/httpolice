# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.known.base import KnownDict
from httpolice.structure import ForwardedParam
from httpolice.syntax import rfc3986, rfc7230, rfc7239


def argument_required(_):       # pragma: no cover
    return True

def no_argument(_):
    return False

def parser_for(name):
    return known.get_info(name).get('parser')


known = KnownDict(ForwardedParam, [
 {'_': ForwardedParam(u'by'),
  '_citations': [RFC(7239, section=(5, 1))],
  'description': u'IP-address of incoming interface of a proxy',
  'parser': rfc7239.node},
 {'_': ForwardedParam(u'for'),
  '_citations': [RFC(7239, section=(5, 2))],
  'description': u'IP-address of client making a request through a proxy',
  'parser': rfc7239.node},
 {'_': ForwardedParam(u'host'),
  '_citations': [RFC(7239, section=(5, 3))],
  'description': u'Host header field of the incoming request',
  'parser': rfc7230.Host},
 {'_': ForwardedParam(u'proto'),
  '_citations': [RFC(7239, section=(5, 4))],
  'description': u'Application protocol used for incoming request',
  'parser': rfc3986.scheme},
], extra_info=['description', 'parser'])
