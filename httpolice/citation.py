# -*- coding: utf-8; -*-


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
