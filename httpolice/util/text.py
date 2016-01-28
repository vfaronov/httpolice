# -*- coding: utf-8; -*-

import string


def nicely_join(strings):
    """
    >>> nicely_join([u'foo'])
    u'foo'
    >>> nicely_join([u'foo', u'bar baz'])
    u'foo and bar baz'
    >>> nicely_join([u'foo', u'bar baz', u'qux'])
    u'foo, bar baz, and qux'
    """
    joined = u''
    for i, s in enumerate(strings):
        if i == len(strings) - 1:
            if len(strings) > 2:
                joined += u'and '
            elif len(strings) > 1:
                joined += u' and '
        joined += s
        if len(strings) > 2 and i < len(strings) - 1:
            joined += u', '
    return joined


# See also http://stackoverflow.com/a/25829509/200445
nonprintable = set([chr(_i) for _i in range(128)]) - set(string.printable)
printable = lambda s: s.translate({ord(c): u'\ufffd' for c in nonprintable})
has_nonprintable = lambda s: \
    len(s) != len(s.translate({ord(c): None for c in nonprintable}))
