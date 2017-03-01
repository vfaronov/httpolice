# -*- coding: utf-8; -*-

"""Classes for representing various elements of the protocol."""

from collections import namedtuple

import six

from httpolice.util.text import force_bytes, force_unicode


###############################################################################
# Commonly useful structures


class _Unavailable(object):

    """
    A placeholder for something that we know is present (**not** missing),
    but we don't know its exact value.
    Used as the singleton :data:`Unavailable`, like `None`.
    """

    __slots__ = ()

    def __repr__(self):
        return 'Unavailable'

    def __eq__(self, other):
        return False

    def __hash__(self):     # pragma: no cover
        return 1

Unavailable = _Unavailable()


def okay(x):
    return (x is not None) and (x is not Unavailable)


class Parametrized(namedtuple('Parametrized', ('item', 'param'))):

    """Anything that consists of some "item" + some parameters to that item."""

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

    def __hash__(self):     # pragma: no cover
        return hash(self.item)


class MultiDict(object):

    """A bunch of key-value pairs where keys are not unique."""

    __slots__ = ('sequence',)

    def __init__(self, sequence=None):
        if sequence is None:
            sequence = []
        self.sequence = sequence

    @property
    def dictionary(self):
        # This is generated on the fly every time,
        # because `self.sequence` can be mutated,
        # e.g. in :class:`httpolice.header.AltSvcView`.
        r = {}
        for k, v in self.sequence:
            r.setdefault(k, []).append(v)
        return r

    def __repr__(self):
        return 'MultiDict(%r)' % self.sequence

    def __eq__(self, other):
        if isinstance(other, MultiDict):
            return self.sequence == other.sequence
        return NotImplemented           # pragma: no cover

    def __ne__(self, other):            # pragma: no cover
        return not (self == other)

    def __getitem__(self, name):
        return self.dictionary[name][0]

    def __contains__(self, name):
        return name in self.dictionary

    def __iter__(self):
        return iter(self.dictionary)

    def __len__(self):
        return len(self.sequence)

    def get(self, name, default=None):
        return self[name] if name in self else default

    def getall(self, name):
        return self.dictionary.get(name, [])

    def duplicates(self):
        return [k for k, v in self.dictionary.items() if len(v) > 1]

    def index(self, name):
        return [k for k, _ in self.sequence].index(name)


@six.python_2_unicode_compatible
class Versioned(namedtuple('Versioned', ('item', 'version'))):

    """Anything that consists of some "item" + a version of that item."""

    __slots__ = ()

    def __str__(self):
        if self.version:
            return u'%s/%s' % self
        else:
            return six.text_type(self.item)


class ProtocolString(six.text_type):

    """Base class for various constant strings used in HTTP."""

    __slots__ = ()

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           six.text_type.__repr__(self))


class CaseInsensitive(ProtocolString):

    __slots__ = ()

    def __eq__(self, other):
        if isinstance(other, six.text_type):
            return self.lower() == other.lower()
        return NotImplemented

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

    """A single header field from the message's headers or trailers.

    A message can have more than one header entry with the same :attr:`name`.
    Contrast with :class:`httpolice.header.HeaderView`.
    """

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

    """A connection option (RFC 7230 Section 6.1)."""

    __slots__ = ()


class MediaType(CaseInsensitive):

    """A media type.

    Although in RFC 7231 a ``media-type`` includes parameters,
    what's mainly interesting for HTTPolice is the media type itself,
    i.e. the ``type/subtype`` pair.

    We could represent it as a tuple, but that's a hopeless rabbit hole,
    because then we would branch out to structured suffixes (like ``+xml``),
    facet prefixes (like ``vnd.``), and so on.
    Instead we have a single string that can be picked apart
    by functions in :mod:`httpolice.known.media_type`.
    """

    __slots__ = ()


class UpgradeToken(ProtocolString):

    """A protocol name for the ``Upgrade`` header (RFC 7230 Section 6.7).

    It is case-sensitive; see https://github.com/httpwg/http11bis/issues/8 .
    """

    __slots__ = ()


class LanguageTag(CaseInsensitive):

    """A language tag (RFC 5646)."""

    __slots__ = ()


class ProductName(ProtocolString):

    """A product name (RFC 7231 Section 5.5.3, 7.4.2)."""

    __slots__ = ()


class Charset(CaseInsensitive):

    __slots__ = ()


class EntityTag(namedtuple('EntityTag', ('weak', 'opaque_tag'))):

    __slots__ = ()

    def weak_equiv(self, other):
        """Weak comparison of entity tags (RFC 7232 Section 2.3.2)."""
        return self.opaque_tag == other.opaque_tag

    def strong_equiv(self, other):
        """Strong comparison of entity tags (RFC 7232 Section 2.3.2)."""
        return not self.weak and not other.weak and \
            self.opaque_tag == other.opaque_tag


class RangeUnit(CaseInsensitive):

    """A range unit (RFC 7233 Section 2)."""

    __slots__ = ()


class RangeSpecifier(namedtuple('RangeSpecifier', ('unit', 'ranges'))):

    """A request range specifier (RFC 7233 Section 3.1)."""

    __slots__ = ()


class ContentRange(namedtuple('ContentRange', ('unit', 'range'))):

    """A response content range (RFC 7233 Section 4.2)."""

    __slots__ = ()


class CacheDirective(CaseInsensitive):

    """A cache directive name (RFC 7234 Section 5.2)."""

    __slots__ = ()


class WarningValue(namedtuple('WarningValue',
                              ('code', 'agent', 'text', 'date'))):

    """A value from a ``Warning`` header (RFC 7234 Section 5.5)."""

    __slots__ = ()

    # Allow comparing directly to warn codes
    # so that we can do stuff like ``299 in msg.headers.warning``
    # (like with :class:`Parametrized`).

    def __eq__(self, other):
        if isinstance(other, tuple):
            return super(WarningValue, self).__eq__(other)
        else:
            return self.code == other

    def __ne__(self, other):        # pragma: no cover
        return not (self == other)

    def __hash__(self):             # pragma: no cover
        return hash(self.code)


class WarnCode(int):

    """A warn code (RFC 7234 Section 5.5)."""

    __slots__ = ()

    def __repr__(self):
        return 'WarnCode(%d)' % self


class AuthScheme(CaseInsensitive):

    __slots__ = ()


class HSTSDirective(CaseInsensitive):

    __slots__ = ()


class RelationType(CaseInsensitive):

    """A registered link relation type (RFC 5988 Section 4)."""

    __slots__ = ()


class ExtValue(namedtuple('ExtValue', ('charset', 'language', 'value_bytes'))):

    """An ``ext-value`` (RFC 5987)."""

    __slots__ = ()


class AltSvcParam(ProtocolString):

    """An ``Alt-Svc`` parameter name (RFC 7838 Section 3)."""

    __slots__ = ()


class Preference(CaseInsensitive):

    """An HTTP preference token (RFC 7240 Section 2)."""

    __slots__ = ()
