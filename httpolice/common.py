# -*- coding: utf-8; -*-

from collections import namedtuple


class ReportNode(object):

    self_name = 'self'

    def __init__(self):
        self.complaints = None
        self.annotated = None

    def complain(self, notice_ident, **kwargs):
        if self.complaints is None:
            self.complaints = []
        context = dict({self.self_name: self}, **kwargs)
        complaint = (notice_ident, context)
        if complaint not in self.complaints:
            self.complaints.append(complaint)


class _Unparseable(object):

    __slots__ = ()

    def __repr__(self):
        return 'Unparseable'

Unparseable = _Unparseable()


def okay(x):
    return (x is not None) and (x is not Unparseable)


class Citation(object):

    __slots__ = ('title', 'url')
    __unicode__ = lambda self: self.title
    __repr__ = lambda self: 'Citation(%r, %r)' % (self.title, self.url)

    def __init__(self, title, url):
        self.title = title
        self.url = url


class RFC(Citation):

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


class Parametrized(namedtuple('Parametrized', ('item', 'param'))):

    __slots__ = ()

    def __eq__(self, other):
        return (self.item == other) or super(Parametrized, self).__eq__(other)

    def __ne__(self, other):
        return (self.item != other) and super(Parametrized, self).__ne__(other)


class OriginForm(ProtocolString):

    __slots__ = ()


class AsteriskForm(ProtocolString):

    __slots__ = ()


class KnownDict(object):

    def __init__(self, items, extra_info=None):
        allowed_info = set(['_', '_citations'] + (extra_info or []))
        self._by_key = {}
        self._by_name = {}
        for item in items:
            assert set(item).issubset(allowed_info)
            key = item['_']
            assert key not in self._by_key
            self._by_key[key] = item
            name = self._name_for(item)
            assert name not in self._by_name
            self._by_name[name] = item

    def __getattr__(self, name):
        if name in self._by_name:
            return self._by_name[name]['_']
        else:
            raise AttributeError(name)

    def __getitem__(self, key):
        return self._by_key[key]

    def get_info(self, key):
        return self._by_key.get(key, {})

    def __iter__(self):
        return iter(self._by_key)

    def __contains__(self, key):
        return key in self._by_key

    @classmethod
    def _name_for(cls, item):
        return item['_'].replace(u'-', u' ').replace(u' ', u'_').lower()
