# -*- coding: utf-8; -*-

from httpolice.citation import RFC
from httpolice.known.base import KnownDict
from httpolice.structure import StatusCode


NOT_AT_ALL = 0
NOT_BY_DEFAULT = 1
BY_DEFAULT = 2


def is_cacheable(code):
    return known.get_info(code).get('cacheable')


known = KnownDict([
 {'_': StatusCode(100),
  '_citations': [RFC(7231, section=(6, 2, 1))],
  '_title': 'Continue',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(101),
  '_citations': [RFC(7231, section=(6, 2, 2))],
  '_title': 'Switching Protocols',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(102),
  '_citations': [RFC(2518)],
  '_title': 'Processing'},
 {'_': StatusCode(200),
  '_citations': [RFC(7231, section=(6, 3, 1))],
  '_title': 'OK',
  'cacheable': BY_DEFAULT},
 {'_': StatusCode(201),
  '_citations': [RFC(7231, section=(6, 3, 2))],
  '_title': 'Created',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(202),
  '_citations': [RFC(7231, section=(6, 3, 3))],
  '_title': 'Accepted',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(203),
  '_citations': [RFC(7231, section=(6, 3, 4))],
  '_title': 'Non-Authoritative Information',
  'cacheable': BY_DEFAULT},
 {'_': StatusCode(204),
  '_citations': [RFC(7231, section=(6, 3, 5))],
  '_title': 'No Content',
  'cacheable': BY_DEFAULT},
 {'_': StatusCode(205),
  '_citations': [RFC(7231, section=(6, 3, 6))],
  '_title': 'Reset Content',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(206),
  '_citations': [RFC(7233, section=(4, 1))],
  '_title': 'Partial Content',
  'cacheable': BY_DEFAULT},
 {'_': StatusCode(207),
  '_citations': [RFC(4918)],
  '_title': 'Multi-Status'},
 {'_': StatusCode(208),
  '_citations': [RFC(5842)],
  '_title': 'Already Reported'},
 {'_': StatusCode(226), '_citations': [RFC(3229)], '_title': 'IM Used'},
 {'_': StatusCode(300),
  '_citations': [RFC(7231, section=(6, 4, 1))],
  '_title': 'Multiple Choices',
  'cacheable': BY_DEFAULT},
 {'_': StatusCode(301),
  '_citations': [RFC(7231, section=(6, 4, 2))],
  '_title': 'Moved Permanently',
  'cacheable': BY_DEFAULT},
 {'_': StatusCode(302),
  '_citations': [RFC(7231, section=(6, 4, 3))],
  '_title': 'Found',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(303),
  '_citations': [RFC(7231, section=(6, 4, 4))],
  '_title': 'See Other',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(304),
  '_citations': [RFC(7232, section=(4, 1))],
  '_title': 'Not Modified',
  # The cacheability story here is a complicated by the fact that
  # a cache can generate a 304 response out of a stored 200 response
  # (as in RFC 7234 section 4.3.2).
  # It's not clear to me whether an ``Age`` header
  # would make sense on such a response,
  # so let's not check it for now.
  'cacheable': None},
 {'_': StatusCode(305),
  '_citations': [RFC(7231, section=(6, 4, 5))],
  '_title': 'Use Proxy'},
 {'_': StatusCode(306),
  '_citations': [RFC(7231, section=(6, 4, 6))],
  '_title': '(Unused)'},
 {'_': StatusCode(307),
  '_citations': [RFC(7231, section=(6, 4, 7))],
  '_title': 'Temporary Redirect',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(308),
  '_citations': [RFC(7538)],
  '_title': 'Permanent Redirect'},
 {'_': StatusCode(400),
  '_citations': [RFC(7231, section=(6, 5, 1))],
  '_title': 'Bad Request',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(401),
  '_citations': [RFC(7235, section=(3, 1))],
  '_title': 'Unauthorized',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(402),
  '_citations': [RFC(7231, section=(6, 5, 2))],
  '_title': 'Payment Required'},
 {'_': StatusCode(403),
  '_citations': [RFC(7231, section=(6, 5, 3))],
  '_title': 'Forbidden',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(404),
  '_citations': [RFC(7231, section=(6, 5, 4))],
  '_title': 'Not Found',
  'cacheable': BY_DEFAULT},
 {'_': StatusCode(405),
  '_citations': [RFC(7231, section=(6, 5, 5))],
  '_title': 'Method Not Allowed',
  'cacheable': BY_DEFAULT},
 {'_': StatusCode(406),
  '_citations': [RFC(7231, section=(6, 5, 6))],
  '_title': 'Not Acceptable',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(407),
  '_citations': [RFC(7235, section=(3, 2))],
  '_title': 'Proxy Authentication Required',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(408),
  '_citations': [RFC(7231, section=(6, 5, 7))],
  '_title': 'Request Timeout',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(409),
  '_citations': [RFC(7231, section=(6, 5, 8))],
  '_title': 'Conflict',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(410),
  '_citations': [RFC(7231, section=(6, 5, 9))],
  '_title': 'Gone',
  'cacheable': BY_DEFAULT},
 {'_': StatusCode(411),
  '_citations': [RFC(7231, section=(6, 5, 10))],
  '_title': 'Length Required',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(412),
  '_citations': [RFC(7232, section=(4, 2))],
  '_title': 'Precondition Failed',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(413),
  '_citations': [RFC(7231, section=(6, 5, 11))],
  '_title': 'Payload Too Large',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(414),
  '_citations': [RFC(7231, section=(6, 5, 12))],
  '_title': 'URI Too Long',
  'cacheable': BY_DEFAULT},
 {'_': StatusCode(415),
  '_citations': [RFC(7231, section=(6, 5, 13)), RFC(7694, section=(3,))],
  '_title': 'Unsupported Media Type',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(416),
  '_citations': [RFC(7233, section=(4, 4))],
  '_title': 'Range Not Satisfiable',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(417),
  '_citations': [RFC(7231, section=(6, 5, 14))],
  '_title': 'Expectation Failed',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(421),
  '_citations': [RFC(7540, section=(9, 1, 2))],
  '_title': 'Misdirected Request'},
 {'_': StatusCode(422),
  '_citations': [RFC(4918)],
  '_title': 'Unprocessable Entity'},
 {'_': StatusCode(423), '_citations': [RFC(4918)], '_title': 'Locked'},
 {'_': StatusCode(424),
  '_citations': [RFC(4918)],
  '_title': 'Failed Dependency'},
 {'_': StatusCode(426),
  '_citations': [RFC(7231, section=(6, 5, 15))],
  '_title': 'Upgrade Required',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(428),
  '_citations': [RFC(6585)],
  '_title': 'Precondition Required',
  'cacheable': NOT_AT_ALL},
 {'_': StatusCode(429),
  '_citations': [RFC(6585)],
  '_title': 'Too Many Requests',
  'cacheable': NOT_AT_ALL},
 {'_': StatusCode(431),
  '_citations': [RFC(6585)],
  '_title': 'Request Header Fields Too Large',
  'cacheable': NOT_AT_ALL},
 {'_': StatusCode(451),
  '_citations': [],
  '_title': 'Unavailable for Legal Reasons'},
 {'_': StatusCode(500),
  '_citations': [RFC(7231, section=(6, 6, 1))],
  '_title': 'Internal Server Error',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(501),
  '_citations': [RFC(7231, section=(6, 6, 2))],
  '_title': 'Not Implemented',
  'cacheable': BY_DEFAULT},
 {'_': StatusCode(502),
  '_citations': [RFC(7231, section=(6, 6, 3))],
  '_title': 'Bad Gateway',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(503),
  '_citations': [RFC(7231, section=(6, 6, 4))],
  '_title': 'Service Unavailable',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(504),
  '_citations': [RFC(7231, section=(6, 6, 5))],
  '_title': 'Gateway Timeout',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(505),
  '_citations': [RFC(7231, section=(6, 6, 6))],
  '_title': 'HTTP Version Not Supported',
  'cacheable': NOT_BY_DEFAULT},
 {'_': StatusCode(506),
  '_citations': [RFC(2295)],
  '_title': 'Variant Also Negotiates'},
 {'_': StatusCode(507),
  '_citations': [RFC(4918)],
  '_title': 'Insufficient Storage'},
 {'_': StatusCode(508),
  '_citations': [RFC(5842)],
  '_title': 'Loop Detected'},
 {'_': StatusCode(510),
  '_citations': [RFC(2774)],
  '_title': 'Not Extended'},
 {'_': StatusCode(511),
  '_citations': [RFC(6585)],
  '_title': 'Network Authentication Required'}
 ],
 name_from_title=True,
 extra_info=['cacheable']
)
