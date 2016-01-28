# -*- coding: utf-8; -*-

from collections import namedtuple


################ Report nodes


class ReportNode(object):

    __slots__ = ('complaints',)

    self_name = 'self'

    def __init__(self):
        self.complaints = None

    def complain(self, notice_ident, **kwargs):
        if self.complaints is None:
            self.complaints = []
        context = dict({self.self_name: self}, **kwargs)
        complaint = (notice_ident, context)
        if complaint not in self.complaints:
            self.complaints.append(complaint)

    @property
    def sub_nodes(self):
        return []

    def collect_complaints(self):
        for node in self.sub_nodes:
            for c in node.collect_complaints():
                yield c
        for c in self.complaints or []:
            yield c


################ Representations of the various elements of the protocol


class _Unparseable(object):

    __slots__ = ()

    def __repr__(self):
        return 'Unparseable'

    def __eq__(self, other):
        return False

Unparseable = _Unparseable()


def okay(x):
    return (x is not None) and (x is not Unparseable)


class Parametrized(namedtuple('Parametrized', ('item', 'param'))):

    __slots__ = ()

    def __eq__(self, other):
        return (self.item == other) or super(Parametrized, self).__eq__(other)

    def __ne__(self, other):
        return (self.item != other) and super(Parametrized, self).__ne__(other)


class Versioned(namedtuple('Versioned', ('item', 'version'))):

    __slots__ = ()

    def __unicode__(self):
        if self.version:
            return u'%s/%s' % self
        else:
            return unicode(self.item)


class ProtocolString(unicode):

    __slots__ = ()

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, unicode.__repr__(self))


class CaseInsensitive(ProtocolString):

    __slots__ = ()

    def __eq__(self, other):
        if isinstance(other, basestring):
            return self.lower() == other.lower()
        else:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.lower())


class HTTPVersion(ProtocolString):

    __slots__ = ()


http10 = HTTPVersion(u'HTTP/1.0')
http11 = HTTPVersion(u'HTTP/1.1')


class Method(ProtocolString):

    __slots__ = ()


class StatusCode(int):

    __slots__ = ()

    def __repr__(self):
        return 'StatusCode(%d)' % self

    informational = property(lambda self: 100 <= self < 199)
    successful = property(lambda self: 200 <= self < 299)
    redirection = property(lambda self: 300 <= self < 399)
    client_error = property(lambda self: 400 <= self < 499)
    server_error = property(lambda self: 500 <= self < 599)


class HeaderEntry(namedtuple('HeaderEntry', ('name', 'value'))):

    __slots__ = ()

    def __new__(cls, name, value):
        return super(HeaderEntry, cls).__new__(cls,
                                               FieldName(name), str(value))

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


class UpgradeToken(CaseInsensitive):

    # RFC 7230 doesn't say that upgrade tokens are case-insensitive.
    # But RFC 6455 does say that for the ``WebSocket`` token,
    # and it would make a lot of sense in general.

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
        return self.code == other or super(WarningValue, self).__eq__(other)

    def __ne__(self, other):
        return self.code != other and super(WarningValue, self).__ne__(other)


class WarnCode(int):

    __slots__ = ()

    def __repr__(self):
        return 'WarnCode(%d)' % self


################ Citations


class Citation(object):

    __slots__ = ('title', 'url')
    __unicode__ = lambda self: self.title or self.url
    __repr__ = lambda self: 'Citation(%r, %r)' % (self.title, self.url)

    def __init__(self, title, url):
        self.title = title
        self.url = url

    def __eq__(self, other):
        return isinstance(other, Citation) and \
            self.title == other.title and self.url == other.url

    def __ne__(self, other):
        return self != other

    def __hash__(self):
        return hash((self.title, self.url))


class RFC(Citation):

    # The reason we do this as a special subclass
    # that remembers the RFC-specific `num`/`section`/`appendix` attributes
    # is because these values, as produced by :mod:`httpolice.tools.iana`,
    # are pretty-printed and copied directly
    # into the source code of the various `httpolice.known` modules,
    # so we want their `repr()` to look nice there.

    __slots__ = ('num', 'section', 'appendix')

    def __repr__(self):
        if self.section:
            return 'RFC(%d, section=%r)' % (self.num, self.section)
        elif self.appendix:
            return 'RFC(%d, appendix=%r)' % (self.num, self.appendix)
        else:
            return 'RFC(%d)' % self.num

    def __init__(self, num, section=None, appendix=None):
        assert not (section and appendix)
        self.num = num
        self.section = section
        self.appendix = appendix
        title = u'RFC %d' % num
        url = u'http://tools.ietf.org/html/rfc%d' % num
        if section or appendix:
            section_text = u'.'.join(unicode(n) for n in section or appendix)
            word1 = u'§' if section else u'appendix'
            word2 = u'section' if section else u'appendix'
            title += u' %s %s' % (word1, section_text)
            url += u'#%s-%s' % (word2, section_text)
        super(RFC, self).__init__(title, url)
