# -*- coding: utf-8; -*-

from collections import namedtuple
import sys

import six

from httpolice.util.text import force_bytes, force_unicode


# Commonly useful structures for representing various elements of the protocol


class _Unavailable(object):

    __slots__ = ()

    def __repr__(self):
        return 'Unavailable'

    def __eq__(self, other):
        return False

    def __hash__(self):
        return 1

Unavailable = _Unavailable()


def okay(x):
    return (x is not None) and (x is not Unavailable)


class Parametrized(namedtuple('Parametrized', ('item', 'param'))):

    __slots__ = ()

    def __eq__(self, other):
        if isinstance(other, tuple):
            return super(Parametrized, self).__eq__(other)
        else:
            return self.item == other

    def __ne__(self, other):
        if isinstance(other, tuple):
            return super(Parametrized, self).__ne__(other)
        else:
            return self.item != other

    def __hash__(self):
        return hash(self.item)

    @property
    def param_names(self):
        return set(name for name, value in self.param or [])


class Versioned(namedtuple('Versioned', ('item', 'version'))):

    __slots__ = ()

    def __unicode__(self):
        if self.version:
            return u'%s/%s' % self
        else:
            return six.text_type(self.item)

    if sys.version_info[0] >= 3:
        __str__ = __unicode__


class Quoted(namedtuple('Quoted', ('item',))):

    __slots__ = ()


class ProtocolString(six.text_type):

    __slots__ = ()

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           six.text_type.__repr__(self))


class CaseInsensitive(ProtocolString):

    __slots__ = ()

    def __eq__(self, other):
        if isinstance(other, six.text_type):
            return self.lower() == other.lower()
        else:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.lower())

    def startswith(self, other):
        return self.lower().startswith(other.lower())

    def endswith(self, other):
        return self.lower().endswith(other.lower())


###############################################################################


# Representations of specific protocol elements


class Exchange(namedtuple('Exchange', ('request', 'responses'))):

    __slots__ = ()


class Message(object):

    __slots__ = ('version', 'header_entries', 'body', 'trailer_entries')

    def __init__(self, version, header_entries, body, trailer_entries=None):
        self.version = HTTPVersion(force_unicode(version)) \
            if version is not None else None
        self.header_entries = [HeaderEntry(k, v)
                               for k, v in header_entries]
        self.body = bytes(body) if okay(body) else body
        self.trailer_entries = [HeaderEntry(k, v)
                                for k, v in trailer_entries or []]


class Request(Message):

    __slots__ = ('scheme', 'method', 'target')

    def __init__(self, scheme, method, target, version, header_entries,
                 body, trailer_entries=None):
        super(Request, self).__init__(version, header_entries,
                                      body, trailer_entries)
        self.scheme = force_unicode(scheme) if scheme is not None else None
        self.method = Method(force_unicode(method))
        self.target = force_unicode(target)

    def __repr__(self):
        return '<Request %s>' % self.method


class Response(Message):

    __slots__ = ('status', 'reason')

    def __init__(self, version, status, reason, header_entries,
                 body, trailer_entries=None):
        super(Response, self).__init__(version, header_entries,
                                       body, trailer_entries)
        self.status = StatusCode(status)
        self.reason = force_unicode(reason) if reason is not None else None

    def __repr__(self):
        return '<Response %d>' % self.status


class HTTPVersion(ProtocolString):

    __slots__ = ()


http10 = HTTPVersion(u'HTTP/1.0')
http11 = HTTPVersion(u'HTTP/1.1')
http2 = HTTPVersion(u'HTTP/2')


class Method(ProtocolString):

    __slots__ = ()


class StatusCode(int):

    __slots__ = ()

    def __repr__(self):
        return 'StatusCode(%d)' % self

    informational = property(lambda self: 100 <= self <= 199)
    successful = property(lambda self: 200 <= self <= 299)
    redirection = property(lambda self: 300 <= self <= 399)
    client_error = property(lambda self: 400 <= self <= 499)
    server_error = property(lambda self: 500 <= self <= 599)


class HeaderEntry(namedtuple('HeaderEntry', ('name', 'value'))):

    __slots__ = ()

    def __new__(cls, name, value):
        return super(HeaderEntry, cls).__new__(cls,
                                               FieldName(force_unicode(name)),
                                               force_bytes(value))

    def __repr__(self):
        return '<HeaderEntry %s>' % self.name


class FieldName(CaseInsensitive):

    __slots__ = ()


class TransferCoding(CaseInsensitive):

    __slots__ = ()


class ContentCoding(CaseInsensitive):

    __slots__ = ()


class ConnectionOption(CaseInsensitive):

    __slots__ = ()


class MediaType(CaseInsensitive):

    """
    Although in RFC 7231 a ``<media-type>`` includes parameters,
    what's mainly interesting for HTTPolice is the media type itself,
    i.e. the ``type/subtype`` pair
    (or ``type/*``, or ``*/*`` -- in the case of the ``Accept`` header,
    although formally a ``*`` matches the production for ``<token>``).

    We could represent this as a tuple, but that's a hopeless rabbit hole,
    because then we would branch out to structured suffixes (like ``+xml``),
    facet prefixes (like ``vnd.``), and so on.
    Instead we have a single string that can be picked apart
    by functions in :mod:`httpolice.known.media_type`.
    """

    __slots__ = ()


class UpgradeToken(ProtocolString):

    # https://github.com/httpwg/http11bis/issues/8

    __slots__ = ()


class LanguageTag(CaseInsensitive):

    __slots__ = ()


class ProductName(ProtocolString):

    __slots__ = ()


class Charset(CaseInsensitive):

    __slots__ = ()


class EntityTag(namedtuple('EntityTag', ('weak', 'opaque_tag'))):

    __slots__ = ()

    def weak_equiv(self, other):
        return self.opaque_tag == other.opaque_tag

    def strong_equiv(self, other):
        return not self.weak and not other.weak and \
            self.opaque_tag == other.opaque_tag


class RangeUnit(CaseInsensitive):

    __slots__ = ()


class RangeSpecifier(namedtuple('RangeSpecifier', ('unit', 'ranges'))):

    __slots__ = ()


class ContentRange(namedtuple('ContentRange', ('unit', 'range'))):

    __slots__ = ()


class CacheDirective(CaseInsensitive):

    __slots__ = ()


class WarningValue(namedtuple('WarningValue',
                              ('code', 'agent', 'text', 'date'))):

    __slots__ = ()

    # Allow comparing directly to warning codes
    # so that we can do stuff like ``299 in msg.headers.warning``
    # (like with :class:`Parametrized`).

    def __eq__(self, other):
        if isinstance(other, tuple):
            return super(WarningValue, self).__eq__(other)
        else:
            return self.code == other

    def __ne__(self, other):
        if isinstance(other, tuple):
            return super(WarningValue, self).__ne__(other)
        else:
            return self.code != other

    def __hash__(self):
        return hash(self.code)


class WarnCode(int):

    __slots__ = ()

    def __repr__(self):
        return 'WarnCode(%d)' % self


class AuthScheme(CaseInsensitive):

    __slots__ = ()


class HSTSDirective(CaseInsensitive):

    __slots__ = ()


class RelationType(CaseInsensitive):

    __slots__ = ()
