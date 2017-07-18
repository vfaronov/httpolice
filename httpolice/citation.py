# -*- coding: utf-8; -*-

import six


@six.python_2_unicode_compatible
class Citation(object):

    """A reference to a relevant document."""

    __slots__ = ('title', 'url')
    __str__ = lambda self: self.title or self.url

    def __init__(self, title, url):
        self.title = title
        self.url = url

    def __eq__(self, other):        # pragma: no cover
        return isinstance(other, Citation) and \
            self.title == other.title and self.url == other.url

    def __ne__(self, other):        # pragma: no cover
        return not self == other

    def subset_of(self, other):     # pragma: no cover
        return self.url == other.url or self.url.startswith(other.url + u'#')

    def __hash__(self):             # pragma: no cover
        return hash((self.title, self.url))


class RFC(Citation):

    """A reference to an RFC document.

    It remembers the RFC-specific information (number, section, etc.),
    which is necessary for saving into CSV files (`Knowledge.unprocess`).
    """

    __slots__ = ('num', 'section', 'appendix', 'errata')

    def __init__(self, num, section=None, appendix=None, errata=None):
        assert bool(section) + bool(appendix) + bool(errata) <= 1
        self.num = num = int(num)
        self.section = section = six.text_type(section) if section else None
        self.appendix = appendix = six.text_type(appendix) if appendix else None
        self.errata = errata = int(errata) if errata else None
        title = u'RFC %d' % num         # no-break space
        if errata:
            title += u' errata'
            url = u'https://www.rfc-editor.org/errata_search.php?eid=%d' % \
                errata
        else:
            url = u'https://tools.ietf.org/html/rfc%d' % num
            if section or appendix:
                word1 = u'§' if section else u'appendix'
                word2 = u'section' if section else u'appendix'
                title += u' %s %s' % (word1, section or appendix)       # nbsp
                url += u'#%s-%s' % (word2, section or appendix)
        super(RFC, self).__init__(title, url)

    def subset_of(self, other):     # pragma: no cover
        return super(RFC, self).subset_of(other) or \
            self.url.startswith(other.url + u'.')
