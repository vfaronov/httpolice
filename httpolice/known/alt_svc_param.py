# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.known.base import KnownDict
from httpolice.structure import AltSvcParam
from httpolice.syntax import rfc7838


def parser_for(name):
    return known.get_info(name).get('parser')


known = KnownDict(AltSvcParam, [
 {'_': AltSvcParam(u'ma'),
  '_citations': [RFC(7838, section=(3, 1))],
  'parser': rfc7838.ma},
 {'_': AltSvcParam(u'persist'),
  '_citations': [RFC(7838, section=(3, 1))],
  'parser': rfc7838.persist}
], extra_info=['parser'])
