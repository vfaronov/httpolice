# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.known.base import KnownDict
from httpolice.structure import HSTSDirective
from httpolice.syntax import rfc6797


NO = 0
OPTIONAL = 1
REQUIRED = 2


def argument_required(name):
    return known.get_info(name).get('argument') == REQUIRED

def no_argument(name):
    return known.get_info(name).get('argument') == NO

def parser_for(name):
    return known.get_info(name).get('parser')


known = KnownDict(HSTSDirective, [
 {'_': HSTSDirective(u'includeSubDomains'),
  '_citations': [RFC(6797, section=(6, 1, 2))],
  'argument': NO},
 {'_': HSTSDirective(u'max-age'),
  '_citations': [RFC(6797, section=(6, 1, 1))],
  'argument': REQUIRED,
  'parser': rfc6797.max_age_value},
], extra_info=['argument', 'parser'])
