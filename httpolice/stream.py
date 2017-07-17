# -*- coding: utf-8; -*-

from httpolice.parse import ParseError


class Stream(object):

    """
    Wraps a file to enable easier reading in terms that are convenient
    for :mod:`httpolice.framing1`, with automatic raising of `ParseError` etc.
    It can also accumulate parsing-related notices until an object is formed
    where they can be dumped with :meth:`dump_complaints`.

    Methods of this class **do not attempt** to uphold the exact same interface
    as similarly-named methods of file objects.
    """

    max_line_length = 16 * 1024

    def __init__(self, file_, name=None):
        self.file = file_
        self.name = name
        self.eof = False
        self.sane = True
        self.complaints = []
        self._currently_parsing = [None]
        self._next_symbol = None

    def parsing(self, symbol):
        self._next_symbol = symbol
        return self

    def __enter__(self):
        self._currently_parsing.append(self._next_symbol)
        return self

    def __exit__(self, _exc_type, _exc_value, _exc_traceback):
        self._currently_parsing.pop()
        return False

    def error(self, position, expected=None):
        self.sane = False
        return ParseError(self.name, position,
                          expected=[(expected, [self._currently_parsing[-1]])])

    @property
    def good(self):
        return self.sane and not self.eof

    def tell(self):
        return self.file.tell()

    def peek(self, n=1):
        return self.file.peek(n)[:n]

    def read(self, n=-1):
        pos = self.tell()
        r = self.file.read(n)
        if self.peek() == b'':
            self.eof = True
        if len(r) < n and n > 0:
            raise self.error(pos, expected=u'at least %d bytes' % n)
        return r

    def readline(self, decode=True):
        pos = self.tell()
        r = self.file.readline(self.max_line_length)
        if self.peek() == b'':
            self.eof = True
        if not r.endswith(b'\n'):
            if len(r) >= self.max_line_length:
                raise self.error(
                    pos,
                    expected=u'no more than %d bytes before end of line' %
                    self.max_line_length)
            raise self.error(pos, expected=u'data terminated by end of line')

        if len(r) >= 2 and r[-2:-1] == b'\r':
            r = r[:-2]
        else:
            self.complain(1224)
            r = r[:-1]

        if decode:
            r = r.decode('iso-8859-1')

        return r

    def readlineend(self):
        pos = self.tell()
        if self.readline(decode=False) != b'':
            raise self.error(pos, expected=u'end of line')

    def complain(self, notice_id, **context):
        self.complaints.append((notice_id, context))

    def dump_complaints(self, complain_func, **extra_context):
        for (notice_id, context) in self.complaints:
            context = dict(extra_context, **context)
            complain_func(notice_id, **context)
        self.complaints[:] = []     # clear
