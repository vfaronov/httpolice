# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.known.base import KnownDict
from httpolice.structure import HSTSDirective
from httpolice.syntax.common import integer


NO = 0
OPTIONAL = 1
REQUIRED = 2


def argument_required(name):
    return known.get_info(name).get('argument') == REQUIRED

def no_argument(name):
    return known.get_info(name).get('argument') == NO

def parser_for(name):
    return known.get_info(name).get('parser')


known = KnownDict([
 {'_': HSTSDirective('includeSubDomains'),
  '_citations': [RFC(6797, section=(6, 1, 2))],
  'argument': NO},
 {'_': HSTSDirective('max-age'),
  '_citations': [RFC(6797, section=(6, 1, 1))],
  'argument': REQUIRED,
  'parser': integer},
], extra_info=['argument', 'parser'])
