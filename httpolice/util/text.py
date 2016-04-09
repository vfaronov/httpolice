# -*- coding: utf-8; -*-

import string

import six


CHAR_NAMES = {
    b'\t': u'tab',
    b'\n': u'LF',
    b'\r': u'CR',
    b' ': u'space',
    b'"': u'double quote (")',
    b"'": u"single quote (')",
    b',': u'comma (,)',
    b'.': u'period (.)',
    b';': u'semicolon (;)',
    b'-': u'dash (-)',
}


def nicely_join(strings):
    """
    >>> print(nicely_join([u'foo']))
    foo
    >>> print(nicely_join([u'foo', u'bar baz']))
    foo and bar baz
    >>> print(nicely_join([u'foo', u'bar baz', u'qux']))
    foo, bar baz, and qux
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
        show = six.unichr
    return [
        (u'%s' % show(p1)) if p1 == p2 else (u'%s–%s' % (show(p1), show(p2)))
        for (p1, p2) in intervals]


def format_chars(chars):
    u"""
    >>> print(format_chars([b'\\x00', b'\\x04', b'\\x05', b'\\x06', b'\\x07',
    ...                     b' ', b'0', b'1', b'2', b'3', b'4', b'5', b'6',
    ...                     b'7', b'8', b'9', b'A', b'B', b'C', b'D', b'E',
    ...                     b'F']))
    A–F or 0–9 or space or 0x00 or 0x04–0x07

    >>> print(format_chars([b'\\t', b' ']))
    tab or space

    >>> print(format_chars([b'!', b'#', b'$', b'%', b'&', b"'", b'*', b'+',
    ...                     b'.', b'0', b'1', b'2', b'3', b'4', b'5', b'6',
    ...                     b'7', b'8', b'9', b'a', b'b', b'c', b'd', b'e']))
    a–e or 0–9 or single quote (') or period (.) or !#$%&*+

    >>> print(format_chars([b'V', b'W', b'X', b'Y', b'Z', b'a', b'b', b'c']))
    V–Z or a–c
    """
    (letters, digits, named, visible, other) = ([], [], [], [], [])
    for c in chars:
        if c.decode('iso-8859-1') in string.ascii_letters:
            letters.append(c)
        elif c.decode('iso-8859-1') in string.digits:
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
