# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.known.base import KnownDict
from httpolice.structure import Preference


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
 {'_': Preference(u'handling'), '_citations': [RFC(7240)]},
 {'_': Preference(u'respond-async'), '_citations': [RFC(7240)]},
 {'_': Preference(u'return'), '_citations': [RFC(7240)]},
 {'_': Preference(u'wait'), '_citations': [RFC(7240)]}
])
