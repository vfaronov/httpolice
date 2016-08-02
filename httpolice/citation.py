# -*- coding: utf-8; -*-

import six


@six.python_2_unicode_compatible
class Citation(object):

    """A reference to a relevant document."""

    __slots__ = ('title', 'url')
    __str__ = lambda self: self.title or self.url
    __repr__ = lambda self: 'Citation(%r, %r)' % (self.title, self.url)

    def __init__(self, title, url):
        self.title = title
        self.url = url

    def __eq__(self, other):        # pragma: no cover
        return isinstance(other, Citation) and \
            self.title == other.title and self.url == other.url

    def __ne__(self, other):        # pragma: no cover
        return not self == other

    def subset_of(self, other):     # pragma: no cover
        return self == other

    def __hash__(self):             # pragma: no cover
        return hash((self.title, self.url))


class RFC(Citation):

    """A reference to an RFC document.

    It remembers the RFC-specific locators (number, section, etc.)
    in order to get a nice `repr` and a correct :meth:`subset_of`,
    which are needed for ``tools/iana.py``.
    """

    __slots__ = ('num', 'section', 'appendix', 'errata')

    def __repr__(self):
        if self.section:
            return 'RFC(%d, section=%r)' % (self.num, self.section)
        elif self.appendix:
            return 'RFC(%d, appendix=%r)' % (self.num, self.appendix)
        elif self.errata:
            return 'RFC(%d, errata=%r)' % (self.num, self.errata)
        else:
            return 'RFC(%d)' % self.num

    def __init__(self, num, section=None, appendix=None, errata=None):
        assert bool(section) + bool(appendix) + bool(errata) <= 1
        self.num = num
        self.section = section
        self.appendix = appendix
        self.errata = errata
        title = u'RFC %d' % num         # no-break space
        if errata:
            title += u' errata'
            url = u'https://www.rfc-editor.org/errata_search.php?eid=%d' % \
                errata
        else:
            url = u'https://tools.ietf.org/html/rfc%d' % num
            if section or appendix:
                section_text = u'.'.join(six.text_type(n)
                                         for n in section or appendix)
                word1 = u'§' if section else u'appendix'
                word2 = u'section' if section else u'appendix'
                title += u' %s %s' % (word1, section_text)     # no-break space
                url += u'#%s-%s' % (word2, section_text)
        super(RFC, self).__init__(title, url)

    @staticmethod
    def parse_sect(s):
        return tuple(int(part) if part.isdigit() else part
                     for part in s.split('.'))

    def subset_of(self, other):     # pragma: no cover
        if self.num != other.num:
            return False
        if other.section:
            return self.section and \
                self.section[:len(other.section)] == other.section
        if other.appendix:
            return self.appendix and \
                self.appendix[:len(other.appendix)] == other.appendix
        if other.errata:
            return self.errata == other.errata
        return True
