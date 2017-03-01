# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.known.base import KnownDict
from httpolice.structure import Preference
from httpolice.syntax import rfc7240


NO = 0
OPTIONAL = 1
REQUIRED = 2


def argument_required(name):
    return known.get_info(name).get('argument') == REQUIRED

def no_argument(name):
    return known.get_info(name).get('argument') == NO

def parser_for(name):
    return known.get_info(name).get('parser')


known = KnownDict(Preference, [
 {'_': Preference(u'handling'), '_citations': [RFC(7240, section=(4, 4))],
  'argument': REQUIRED, 'parser': rfc7240.handling},
 {'_': Preference(u'respond-async'), '_citations': [RFC(7240, section=(4, 1))],
  'argument': NO},
 {'_': Preference(u'return'), '_citations': [RFC(7240, section=(4, 2))],
  'argument': REQUIRED, 'parser': rfc7240.return_},
 {'_': Preference(u'wait'), '_citations': [RFC(7240, section=(4, 3))],
  'argument': REQUIRED, 'parser': rfc7240.wait}
], extra_info=['argument', 'parser'])
