# -*- coding: utf-8; -*-

import io
import re
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


def force_unicode(x):
    if isinstance(x, bytes):
        return x.decode('iso-8859-1')
    else:
        return six.text_type(x)


def force_bytes(x):
    if isinstance(x, bytes):
        return x
    else:
        return x.encode('iso-8859-1', 'replace')


def stdio_as_bytes(f):
    # Accommodate Python 2 vs. 3 difference.
    return f.buffer if hasattr(f, 'buffer') else f


class WriteIfAny(io.StringIO):

    """
    >>> import sys
    >>> with write_if_any(u'foo\\n', sys.stdout) as buf:
    ...     pass
    ... 
    >>> with write_if_any(u'foo\\n', sys.stdout) as buf:
    ...     n = buf.write(u'bar\\n')
    ... 
    foo
    bar
    """

    def __init__(self, beginning, parent_file):
        super(WriteIfAny, self).__init__()
        self.beginning = beginning
        self.parent_file = parent_file

    def __enter__(self):
        return self

    def __exit__(self, exc_type, _1, _2):
        if exc_type is None:
            value = self.getvalue()
            if value:
                self.parent_file.write(self.beginning + value)
        return False


write_if_any = WriteIfAny


def ellipsize(s, max_length=60):
    """
    >>> print(ellipsize(u'lorem ipsum dolor sit amet', 40))
    lorem ipsum dolor sit amet
    >>> print(ellipsize(u'lorem ipsum dolor sit amet', 20))
    lorem ipsum dolor...
    """
    if len(s) > max_length:
        ellipsis = u'...'
        return s[:(max_length - len(ellipsis))] + ellipsis
    else:
        return s


def detypographize(s):
    u"""
    >>> print(detypographize(u'“Foo bar—baz ‘qux’—xyzzy”: A–Z'))
    "Foo bar--baz 'qux'--xyzzy": A-Z
    """
    return (s.
            replace(u'“', u'"').replace(u'”', u'"').
            replace(u'‘', u"'").replace(u'’', u"'").
            replace(u'—', u'--').                       # em dash
            replace(u'–', u'-').                        # en dash
            replace(u'−', u'-').                        # minus sign
            replace(u' ', u' '))                        # no-break space



def printable(s):
    # Based on `XML 1.0 section 2.2 <https://www.w3.org/TR/xml/#charsets>`_,
    # with the addition of U+0085,
    # which the W3C (Nu) validator also marked as a "forbidden code point".
    # Even with this code, the validator still complains about
    # "Text run is not in Unicode Normalization Form C"
    # and "Document uses the Unicode Private Use Area(s)".
    return re.sub(
        pattern=(u'[\u0000-\u0008\u000B\u000C\u000E-\u001F'
                 u'\u007F-\u009F\uD800-\uDFFF\uFDD0-\uFDEF\uFFFE\uFFFF]'),
        repl=u'\N{REPLACEMENT CHARACTER}',
        string=s
    )


def is_ascii(s):
    u"""
    >>> is_ascii(u'The quick brown fox jumps over the lazy dog.')
    True
    >>> is_ascii(u'Liberté, égalité, fraternité!')
    False
    """
    try:
        s.encode('ascii')
        return True
    except UnicodeError:
        return False


def normalize_whitespace(s):
    """
    >>> print(normalize_whitespace(u'Efficient XML \\n        Interchange'))
    Efficient XML Interchange
    """
    return re.sub(u'\\s+', u' ', s)


class MockStdio(object):

    """Suitable as a mock stdout/stderr for tests under both Python 2 and 3."""

    def __init__(self):
        self.buffer = io.BytesIO()

    def write(self, s):
        self.buffer.write(s.encode('utf-8'))


def contains_percent_encodes(s):
    """
    >>> contains_percent_encodes(u'foo%E2%80%94bar')
    True
    >>> contains_percent_encodes(u'100% natural')
    False
    """
    return bool(re.search(u'%[0-9A-Fa-f]{2}', s))
