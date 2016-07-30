# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.known.base import KnownDict
from httpolice.structure import CacheDirective
from httpolice.syntax import rfc7230, rfc7234


TOKEN_PREFERRED = 0
QUOTED_STRING_PREFERRED = 1

NO = 0
OPTIONAL = 1
REQUIRED = 2


def is_for_request(name):
    return known.get_info(name).get('for_request')

def is_for_response(name):
    return known.get_info(name).get('for_response')

def argument_required(name):
    return known.get_info(name).get('argument') == REQUIRED

def no_argument(name):
    return known.get_info(name).get('argument') == NO

def token_preferred(name):
    return known.get_info(name).get('argument_form') == TOKEN_PREFERRED

def quoted_string_preferred(name):
    return known.get_info(name).get('argument_form') == QUOTED_STRING_PREFERRED

def parser_for(name):
    return known.get_info(name).get('parser')


# A few of these directives (such as ``no-cache``) actually have
# different citations for requests and for responses;
# but it's hard for us to know whether a given instance of ``CacheDirective``
# refers to a request directive or a response directive,
# so we have to use one, more general citation.

known = KnownDict(CacheDirective, [
 {'_': CacheDirective(u'max-age'),
  '_citations': [RFC(7234, section=(5, 2))],
  '_no_sync': ['_citations'],
  'argument': REQUIRED,
  'argument_form': TOKEN_PREFERRED,
  'for_request': True,
  'for_response': True,
  'parser': rfc7234.delta_seconds},
 {'_': CacheDirective(u'max-stale'),
  '_citations': [RFC(7234, section=(5, 2, 1, 2))],
  'argument': OPTIONAL,
  'argument_form': TOKEN_PREFERRED,
  'for_request': True,
  'for_response': False,
  'parser': rfc7234.delta_seconds},
 {'_': CacheDirective(u'min-fresh'),
  '_citations': [RFC(7234, section=(5, 2, 1, 3))],
  'argument': REQUIRED,
  'argument_form': TOKEN_PREFERRED,
  'for_request': True,
  'for_response': False,
  'parser': rfc7234.delta_seconds},
 {'_': CacheDirective(u'must-revalidate'),
  '_citations': [RFC(7234, section=(5, 2, 2, 1))],
  'argument': NO,
  'for_request': False,
  'for_response': True},
 {'_': CacheDirective(u'no-cache'),
  '_citations': [RFC(7234, section=(5, 2))],
  '_no_sync': ['_citations'],
  'argument': OPTIONAL,
  'argument_form': QUOTED_STRING_PREFERRED,
  'for_request': True,
  'for_response': True,
  'parser': rfc7230.comma_list(rfc7230.field_name)},
 {'_': CacheDirective(u'no-store'),
  '_citations': [RFC(7234, section=(5, 2))],
  '_no_sync': ['_citations'],
  'argument': NO,
  'for_request': True,
  'for_response': True},
 {'_': CacheDirective(u'no-transform'),
  '_citations': [RFC(7234, section=(5, 2))],
  '_no_sync': ['_citations'],
  'argument': NO,
  'for_request': True,
  'for_response': True},
 {'_': CacheDirective(u'only-if-cached'),
  '_citations': [RFC(7234, section=(5, 2, 1, 7))],
  'argument': NO,
  'for_request': True,
  'for_response': False},
 {'_': CacheDirective(u'private'),
  '_citations': [RFC(7234, section=(5, 2, 2, 6))],
  'argument': OPTIONAL,
  'argument_form': QUOTED_STRING_PREFERRED,
  'for_request': False,
  'for_response': True,
  'parser': rfc7230.comma_list(rfc7230.field_name)},
 {'_': CacheDirective(u'proxy-revalidate'),
  '_citations': [RFC(7234, section=(5, 2, 2, 7))],
  'argument': NO,
  'for_request': False,
  'for_response': True},
 {'_': CacheDirective(u'public'),
  '_citations': [RFC(7234, section=(5, 2, 2, 5))],
  'argument': NO,
  'for_request': False,
  'for_response': True},
 {'_': CacheDirective(u's-maxage'),
  '_citations': [RFC(7234, section=(5, 2, 2, 9))],
  'argument': REQUIRED,
  'argument_form': TOKEN_PREFERRED,
  'for_request': False,
  'for_response': True,
  'parser': rfc7234.delta_seconds},
 {'_': CacheDirective(u'stale-if-error'),
  '_citations': [RFC(5861, section=(4,))],
  'argument': REQUIRED,
  'for_request': True,
  'for_response': True,
  'parser': rfc7234.delta_seconds},
 {'_': CacheDirective(u'stale-while-revalidate'),
  '_citations': [RFC(5861, section=(3,))],
  'argument': REQUIRED,
  'for_request': False,
  'for_response': True,
  'parser': rfc7234.delta_seconds},
], extra_info=['argument', 'argument_form', 'for_request', 'for_response',
               'parser'])
