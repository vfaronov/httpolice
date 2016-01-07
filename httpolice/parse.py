# -*- coding: utf-8; -*-

from httpolice.common import CaseInsensitive


class Ignore(object):

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return 'Ignore(%r)' % self.value


class ParseError(Exception):

    pass


class MismatchError(ParseError):

    def __init__(self, pos, expected, found):
        super(MismatchError, self).__init__(
            u'at byte position %d: expected %s - found %r' %
            (pos, expected, found))
        self.pos = pos
        self.expected = expected
        self.found = found


class State(object):

    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.stack = []

    def push(self):
        self.stack.append(self.pos)

    def pop(self):
        self.pos = self.stack.pop()

    def discard(self):
        self.stack.pop()

    def is_eof(self):
        return not self.peek()

    def consume(self, s, case_insensitive=False):
        present = self.data[self.pos : self.pos + len(s)]
        if (present == s) or \
                (case_insensitive and present.lower() == s.lower()):
            self.pos += len(present)
            return present
        return None

    def consume_anything(self, n=None):
        if n is None:
            s = self.data[self.pos:]
        else:
            s = self.data[self.pos : self.pos + n]
        self.pos += len(s)
        return s

    def peek(self, n=1):
        return self.data[self.pos : self.pos + n]


def parsify(inner):
    if isinstance(inner, str):
        return LiteralParser(inner)
    else:
        return inner


class Parser(object):

    def parse(self, state):
        raise NotImplementedError

    def __ror__(self, other):
        return AlternativeParser([parsify(other), self])

    def __or__(self, other):
        return AlternativeParser([self, parsify(other)])

    def __add__(self, other):
        return SequenceParser([self, parsify(other)])

    def __radd__(self, other):
        return SequenceParser([parsify(other), self])

    def __invert__(self):
        return WrapParser(Ignore, self)

    def __floordiv__(self, name):
        return NamedParser(name, self)


class EOFParser(object):

    def parse(self, state):
        if not state.is_eof():
            raise MismatchError(state.pos, u'end of data', state.peek(5))
        return Ignore(None)


class FuncParser(Parser):

    def __init__(self, func):
        super(FuncParser, self).__init__()
        self.func = func

    def parse(self, state):
        return self.func(state)


class NBytesParser(Parser):

    def __init__(self, min_n=None, max_n=None):
        super(NBytesParser, self).__init__()
        self.min_n = min_n
        self.max_n = max_n

    def parse(self, state):
        state.push()
        s = state.consume_anything(self.max_n)
        if (self.min_n is not None) and (len(s) < self.min_n):
            state.pop()
            raise ParseError(u'at byte position %d: '
                             u'expected at least %d more bytes, '
                             u'but only %d remaining' %
                             (state.pos, self.min_n, len(s)))
        else:
            state.discard()
            return s


class NamedParser(Parser):

    def __init__(self, name, inner):
        super(NamedParser, self).__init__()
        self.name = name
        self.inner = parsify(inner)

    def parse(self, state):
        pos = state.pos
        try:
            return self.inner.parse(state)
        except MismatchError, e:
            if e.pos == pos:
                raise MismatchError(e.pos, self.name, e.found)
            else:
                raise


class LiteralParser(Parser):

    def __init__(self, s, case_insensitive=False):
        super(LiteralParser, self).__init__()
        self.literal = s
        self.case_insensitive = case_insensitive

    def parse(self, state):
        s = state.consume(self.literal, self.case_insensitive)
        if s:
            return s
        else:
            raise MismatchError(state.pos, u'%r' % self.literal,
                                state.peek(len(self.literal)))


class CharClassParser(Parser):

    def __init__(self, chars):
        super(CharClassParser, self).__init__()
        self.chars = chars

    def parse(self, state):
        c = state.peek()
        if c and (c in self.chars):
            return state.consume(c)
        else:
            raise MismatchError(state.pos, u'one of %r' % self.chars, c)


class SequenceParser(Parser):

    def __init__(self, inners):
        super(SequenceParser, self).__init__()
        self.inners = [parsify(inner) for inner in inners]

    def parse(self, state):
        rs = []
        for inner in self.inners:
            r = inner.parse(state)
            if not isinstance(r, Ignore):
                rs.append(r)
        if len(rs) == 1:
            return rs[0]
        else:
            return tuple(rs)

    def __add__(self, other):
        return SequenceParser(self.inners + [other])


class AlternativeParser(Parser):

    def __init__(self, inners):
        super(AlternativeParser, self).__init__()
        self.inners = [parsify(inner) for inner in inners]

    def parse(self, state):
        errors = []
        for inner in self.inners:
            state.push()
            try:
                r = inner.parse(state)
            except ParseError, e:
                state.pop()
                errors.append(e)
            else:
                state.discard()
                return r
        max_pos = max(e.pos for e in errors)
        best_errors = sorted((e for e in errors if e.pos == max_pos),
                             key=lambda e: len(e.found), reverse=True)
        raise MismatchError(max_pos,
                            u' or '.join(e.expected for e in best_errors),
                            best_errors[0].found)

    def __or__(self, other):
        return AlternativeParser(self.inners + [other])


class TimesParser(Parser):

    def __init__(self, min_, max_, inner):
        super(TimesParser, self).__init__()
        self.min_ = min_
        self.max_ = max_
        self.inner = parsify(inner)

    def parse(self, state):
        r = []
        while (self.max_ is None) or (len(r) < self.max_):
            state.push()
            try:
                r.append(self.inner.parse(state))
            except ParseError:
                state.pop()
                if (self.min_ is None) or (len(r) >= self.min_):
                    return r
                else:
                    raise
            else:
                state.discard()
        return r


class WrapParser(Parser):

    def __init__(self, func, inner):
        super(WrapParser, self).__init__()
        self.func = func
        self.inner = parsify(inner)

    def parse(self, state):
        r = self.inner.parse(state)
        return self.func(r)


eof = EOFParser()
function = FuncParser
nbytes = NBytesParser
anything = nbytes(None, None)
wrap = WrapParser
argwrap = lambda func, inner: wrap(lambda args: func(*args), inner)
subst = lambda s, inner: wrap(lambda _: s, inner)
maybe = lambda inner, empty=None: inner | function(lambda _: empty)
literal = LiteralParser
char_class = CharClassParser
times = TimesParser
many = lambda inner: times(0, None, inner)
many1 = lambda inner: times(1, None, inner)
join = lambda inner: wrap(''.join, inner)
string = lambda inner: join(many(inner))
string1 = lambda inner: join(many1(inner))
decode = lambda inner: wrap(lambda s: s.decode('utf-8', 'replace'), inner)
decode_into = lambda con, inner: wrap(con, decode(inner))
ci = lambda s: decode_into(CaseInsensitive, literal(s, case_insensitive=True))

rfc = lambda num, rule: u'<%s> (RFC %d)' % (rule, num)
char_range = lambda min_, max_: ''.join(chr(x) for x in range(min_, max_ + 1))
