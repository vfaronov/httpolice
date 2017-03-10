# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.known.base import KnownDict
from httpolice.structure import Method


def defines_body(name):
    return known.get_info(name).get('defines_body')

def is_cacheable(name):
    return known.get_info(name).get('cacheable')

def is_safe(name):
    return known.get_info(name).get('safe')


class KnownMethods(KnownDict):

    def __init__(self, *args, **kwargs):
        super(KnownMethods, self).__init__(Method, *args, **kwargs)

    @classmethod
    def _name_for(cls, item):
        return item['_'].replace(u'-', u'_')


# When adding a new method, fill in the fields as follows:
#
#   ``_``, ``_citations``, ``safe``, ``idempotent``
#     Obvious, and usually filled by ``tools/iana.py``.
#
#   ``defines_body``
#     Whether a meaning is defined for a payload body with this method.
#     (For example, RFC 7231 Section 4.3.1 says
#     "a payload within a GET request message has no defined semantics",
#     so ``defines_body`` is ``False``.)
#
#   ``cacheable``
#     Whether responses to this method can be cached (RFC 7234).

known = KnownMethods([
 {'_': Method(u'ACL'),
  '_citations': [RFC(3744, section=(8, 1))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'BASELINE-CONTROL'),
  '_citations': [RFC(3253, section=(12, 6))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'BIND'),
  '_citations': [RFC(5842, section=(4,))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'CHECKIN'),
  '_citations': [RFC(3253, section=(4, 4))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'CHECKOUT'),
  '_citations': [RFC(3253, section=(4, 3))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'CONNECT'),
  '_citations': [RFC(7231, section=(4, 3, 6))],
  'cacheable': False,
  'defines_body': False,
  'idempotent': False,
  'safe': False},
 {'_': Method(u'COPY'),
  '_citations': [RFC(4918, section=(9, 8))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'DELETE'),
  '_citations': [RFC(7231, section=(4, 3, 5))],
  'cacheable': False,
  'defines_body': False,
  'idempotent': True,
  'safe': False},
 {'_': Method(u'GET'),
  '_citations': [RFC(7231, section=(4, 3, 1))],
  'cacheable': True,
  'defines_body': False,
  'idempotent': True,
  'safe': True},
 {'_': Method(u'HEAD'),
  '_citations': [RFC(7231, section=(4, 3, 2))],
  'cacheable': True,
  'defines_body': False,
  'idempotent': True,
  'safe': True},
 {'_': Method(u'LABEL'),
  '_citations': [RFC(3253, section=(8, 2))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'LINK'),
  '_citations': [RFC(2068, section=(19, 6, 1, 2))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'LOCK'),
  '_citations': [RFC(4918, section=(9, 10))],
  'idempotent': False,
  'safe': False},
 {'_': Method(u'MERGE'),
  '_citations': [RFC(3253, section=(11, 2))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'MKACTIVITY'),
  '_citations': [RFC(3253, section=(13, 5))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'MKCALENDAR'),
  '_citations': [RFC(4791, section=(5, 3, 1))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'MKCOL'),
  '_citations': [RFC(4918, section=(9, 3)), RFC(5689, section=(3,))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'MKREDIRECTREF'),
  '_citations': [RFC(4437, section=(6,))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'MKWORKSPACE'),
  '_citations': [RFC(3253, section=(6, 3))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'MOVE'),
  '_citations': [RFC(4918, section=(9, 9))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'OPTIONS'),
  '_citations': [RFC(7231, section=(4, 3, 7))],
  'cacheable': False,
  'idempotent': True,
  'safe': True},
 {'_': Method(u'ORDERPATCH'),
  '_citations': [RFC(3648, section=(7,))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'PATCH'),
  '_citations': [RFC(5789, section=(2,))],
  'cacheable': False,
  'defines_body': True,
  'idempotent': False,
  'safe': False},
 {'_': Method(u'POST'),
  '_citations': [RFC(7231, section=(4, 3, 3))],
  'cacheable': True,
  'defines_body': True,
  'idempotent': False,
  'safe': False},
 {'_': Method(u'PRI'),
  '_citations': [RFC(7540, section=(3, 5))],
  'idempotent': True,
  'safe': True},
 {'_': Method(u'PROPFIND'),
  '_citations': [RFC(4918, section=(9, 1))],
  'defines_body': True,
  'idempotent': True,
  'safe': True},
 {'_': Method(u'PROPPATCH'),
  '_citations': [RFC(4918, section=(9, 2))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'PUT'),
  '_citations': [RFC(7231, section=(4, 3, 4))],
  'cacheable': False,
  'defines_body': True,
  'idempotent': True,
  'safe': False},
 {'_': Method(u'REBIND'),
  '_citations': [RFC(5842, section=(6,))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'REPORT'),
  '_citations': [RFC(3253, section=(3, 6))],
  'idempotent': True,
  'safe': True},
 {'_': Method(u'SEARCH'),
  '_citations': [RFC(5323, section=(2,))],
  'idempotent': True,
  'safe': True},
 {'_': Method(u'TRACE'),
  '_citations': [RFC(7231, section=(4, 3, 8))],
  'cacheable': False,
  'defines_body': False,
  'idempotent': True,
  'safe': True},
 {'_': Method(u'UNBIND'),
  '_citations': [RFC(5842, section=(5,))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'UNCHECKOUT'),
  '_citations': [RFC(3253, section=(4, 5))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'UNLINK'),
  '_citations': [RFC(2068, section=(19, 6, 1, 3))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'UNLOCK'),
  '_citations': [RFC(4918, section=(9, 11))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'UPDATE'),
  '_citations': [RFC(3253, section=(7, 1))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'UPDATEREDIRECTREF'),
  '_citations': [RFC(4437, section=(7,))],
  'idempotent': True,
  'safe': False},
 {'_': Method(u'VERSION-CONTROL'),
  '_citations': [RFC(3253, section=(3, 5))],
  'idempotent': True,
  'safe': False}
 ],
 extra_info=['cacheable', 'defines_body', 'idempotent', 'safe']
)
