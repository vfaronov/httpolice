# -*- coding: utf-8; -*-

import string


CHAR_NAMES = {
    '\t': u'tab',
    '\n': u'LF',
    '\r': u'CR',
    ' ': u'space',
    '"': u'double quote (")',
    "'": u"single quote (')",
    ',': u'comma (,)',
    '.': u'period (.)',
    ';': u'semicolon (;)',
    '-': u'dash (-)',
}


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


def _char_ranges(chars, as_hex=False):
    intervals = []
    min_ = max_ = None
    for c in chars:
        point = ord(c)
        if max_ == point - 1:
            max_ = point
        else:
            if min_ is not None:
                intervals.append((min_, max_))
            min_ = max_ = point
    if min_ is not None:
        intervals.append((min_, max_))
    if as_hex:
        show = lambda point: u'%#04x' % point
    else:
        show = lambda point: chr(point).decode('ascii')
    return [
        (u'%s' % show(p1)) if p1 == p2 else (u'%s–%s' % (show(p1), show(p2)))
        for (p1, p2) in intervals]


def format_chars(chars):
    r"""
    >>> format_chars('\x00\x04\x05\x06\x07 0123456789ABCDEF')
    u'A\u2013F or 0\u20139 or space or 0x00 or 0x04\u20130x07'

    >>> format_chars('\t ')
    u'tab or space'

    >>> format_chars("!#$%&'*+.0123456789abcdef")
    u"a\u2013f or 0\u20139 or single quote (') or period (.) or !#$%&*+"

    >>> format_chars('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
    u'A\u2013Z or a\u2013z'
    """
    (letters, digits, named, visible, other) = ([], [], [], [], [])
    for c in chars:
        if c in string.ascii_letters:
            letters.append(c)
        elif c in string.digits:
            digits.append(c)
        elif c in CHAR_NAMES:
            named.append(c)
        elif 0x21 <= ord(c) < 0x7F:
            visible.append(c)
        else:
            other.append(c)
    pieces = (_char_ranges(letters) + _char_ranges(digits) +
              [CHAR_NAMES[c] for c in named] +
              [u''.join(c.decode('ascii') for c in visible)] +
              _char_ranges(other, as_hex=True))
    return u' or '.join(piece for piece in pieces if piece)


# See also http://stackoverflow.com/a/25829509/200445
nonprintable = set([chr(_i) for _i in range(128)]) - set(string.printable)
printable = lambda s: s.translate({ord(c): u'\ufffd' for c in nonprintable})
has_nonprintable = lambda s: printable(s) != s
