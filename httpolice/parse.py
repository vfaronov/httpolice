# -*- coding: utf-8; -*-

"""A library of parser combinators based on the Earley algorithm.

Examples of usage can be found in :mod:`httpolice.syntax`.

Why do we use Earley instead of a more mainstream approach like LR(1)?
Because Earley can deal with any (context-free) grammar.
So we can use the rules almost exactly as defined in the RFCs.
We don't need to transform them, add lookaheads etc.
They just work. And we get detailed error messages for free.

However, Earley is not very fast (at least this implementation).
We use it for headers, which have complex grammars but are easy to memoize.
For HTTP/1.x message framing, we just use regexes,
which are derived automatically from the same code (:meth:`Symbol.as_regex`).

A parser's input is a stream of bytes, represented by :class:`Stream`.
The output is whatever is returned by the semantic actions
(the ``<<`` operator, :meth:`Symbol.__rlshift__`).
Before applying semantic actions,
bytes are automatically decoded from ISO-8859-1--the historic encoding of HTTP.

If a semantic action is marked with the :func:`can_complain` decorator,
then it can also produce complaints (notices).
For example, this is how notice 1015 is implemented.
Only the parser sees the ``BWS``,
but its complaint is propagated up to the message where the ``BWS`` was found.

Also, the input string can be annotated with parsed objects.
For example, in an HTML report,
the ``text/xml`` in ``Accept: text/xml;q=0.9`` becomes a hyperlink to RFC,
because it is parsed into a :class:`~httpolice.structure.MediaType` object.
The list of classes to annotate must be passed to :meth:`Stream.parse`.
Also, the object (in this case, ``MediaType(u'text/xml')``)
must be the end result of a distinct :class:`Nonterminal`,
**not** buried inside some :class:`Rule`.
The ``<<`` operator (:meth:`Symbol.__rlshift__`)
ensures this automatically for most classes.
"""

from collections import OrderedDict
import operator
import re

from bitstring import BitArray, Bits
import six

from httpolice.structure import Unavailable
from httpolice.util.text import format_chars


###############################################################################
# Combinators to construct a grammar suitable for the Earley algorithm.


class Symbol(object):

    """A symbol of the grammar (either terminal or nonterminal)."""

    def __init__(self, name=None, citation=None, is_pivot=False,
                 is_ephemeral=None):
        self.name = name
        self.citation = citation
        self.is_pivot = is_pivot
        self._is_ephemeral = is_ephemeral
        self._regex = None
        self._compiled_regex = None

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__,
                            self.name or hex(id(self)))

    def __gt__(self, seal):
        """``sym >seal`` seals the `sym` symbol, then applies `seal` to it.

        After a symbol is sealed, it is treated as a unit,
        never inlined into other symbols' rules.
        If every "top-level" symbol is sealed,
        the actual grammar is structured exactly as seen in the code.
        This is also necessary for error reporting.
        See also :func:`fill_names`.
        """
        if self.name is None:
            sealed = self
        else:
            sealed = SimpleNonterminal(rules=[Rule((self,))])
        (sealed.name, sealed.citation, sealed.is_pivot) = seal
        return sealed

    @property
    def is_ephemeral(self):
        if self._is_ephemeral is None:
            return (self.name is None)
        else:
            return self._is_ephemeral

    def as_compiled_regex(self):
        if self._compiled_regex is None:
            self._compiled_regex = re.compile(self.as_regex())
        return self._compiled_regex

    def as_regex(self):
        if self._regex is None:
            self._regex = self.build_regex()
        return self._regex

    def build_regex(self):
        raise NotImplementedError

    def group(self):
        raise NotImplementedError

    def is_nullable(self):
        raise NotImplementedError

    def as_rule(self):
        raise NotImplementedError

    def as_rules(self):
        raise NotImplementedError

    def as_nonterminal(self):
        raise NotImplementedError

    def __or__(self, other):
        other = as_symbol(other)
        return SimpleNonterminal(rules=self.as_rules() + other.as_rules())

    def __ror__(self, other):
        other = as_symbol(other)
        return SimpleNonterminal(rules=other.as_rules() + self.as_rules())

    def __mul__(self, other):
        other = as_symbol(other)
        return SimpleNonterminal(
            rules=[self.as_rule().concat(other.as_rule())])

    def __rmul__(self, other):
        other = as_symbol(other)
        return SimpleNonterminal(
            rules=[other.as_rule().concat(self.as_rule())])

    def __rlshift__(self, func):
        """``func << sym`` wraps the result of parsing `sym` with `func`."""
        if isinstance(func, type) and not (func is int or func is float or
                                           func is six.text_type):
            is_ephemeral = False
        else:
            is_ephemeral = None
        return SimpleNonterminal(
            rules=[rule.wrap(func) for rule in self.as_rules()],
            is_ephemeral=is_ephemeral)

    def __add__(self, other):
        return operator.add << self * other

    def __radd__(self, other):
        return operator.add << other * self

    def __mod__(self, other):
        return _continue_right_list << self * other


class Terminal(Symbol):

    """A terminal symbol of the grammar."""

    def __init__(self, name=None, citation=None, bits=None):
        super(Terminal, self).__init__(name, citation, is_pivot=False)
        self.bits = bits if bits is not None else Bits(256)

    def chars(self):
        return [six.int2byte(i) for (i, v) in enumerate(self.bits) if v]

    def match(self, char):
        return self.bits[ord(char)]

    def group(self):
        return self

    def build_regex(self):
        return b'[' + b''.join(re.escape(char) for char in self.chars()) + b']'

    def as_rule(self):
        return Rule((self,))

    def as_rules(self):
        return [self.as_rule()]

    def as_nonterminal(self):
        return SimpleNonterminal(rules=self.as_rules())

    def __or__(self, other):
        other = as_symbol(other)
        if isinstance(other, Terminal):
            return Terminal(bits=self.bits | other.bits)
        else:
            return super(Terminal, self).__or__(other)

    def __sub__(self, other):
        other = as_symbol(other)
        return Terminal(bits=self.bits ^ (self.bits & other.bits))

    def is_nullable(self):
        return False


class Nonterminal(Symbol):

    """A nonterminal symbol of the grammar.

    Every nonterminal has a list of rules (:class:`Rule` objects)
    according to which it can be parsed.
    This list can be static (as in :class:`SimpleNonterminal`)
    or generated on the fly (as in :class:`RepeatedNonterminal`).
    """

    def __init__(self, name=None, citation=None, is_pivot=False,
                 is_ephemeral=None):
        super(Nonterminal, self).__init__(name, citation, is_pivot,
                                          is_ephemeral)
        self._is_nullable = None

    @property
    def rules(self):
        raise NotImplementedError

    def build_regex(self):
        return b'(' + b'|'.join(b''.join(sym.as_regex() for sym in rule.symbols)
                                for rule in self.rules) + b')'

    def as_rule(self):
        if self.is_ephemeral and len(self.rules) == 1:
            return self.rules[0]
        else:
            return Rule((self,))

    def as_rules(self):
        if self.is_ephemeral:
            return self.rules
        else:
            return [self.as_rule()]

    def as_nonterminal(self):
        return self

    def is_nullable(self):
        if self._is_nullable is None:
            self._is_nullable = any(all(sym.is_nullable()
                                        for sym in rule.symbols)
                                    for rule in self.rules)
        return self._is_nullable


class SimpleNonterminal(Nonterminal):

    def __init__(self, name=None, citation=None, is_pivot=False,
                 is_ephemeral=None, rules=None):
        super(SimpleNonterminal, self).__init__(name, citation, is_pivot,
                                                is_ephemeral)
        if rules is None:
            rules = []
        self._rules = rules

    @property
    def rules(self):
        return self._rules

    def group(self):
        if self.is_ephemeral:
            return SimpleNonterminal(rules=self.rules, is_ephemeral=False)
        else:
            return self

    def set_rules_from(self, other):
        self._rules = other.rules

    rec = property(None, set_rules_from)


class RepeatedNonterminal(Nonterminal):

    def __init__(self, name=None, citation=None, max_count=None, inner=None):
        super(RepeatedNonterminal, self).__init__(name, citation,
                                                  is_pivot=False,
                                                  is_ephemeral=False)
        self.max_count = max_count
        self.inner = inner
        self._rules = None

    def group(self):    # pragma: no cover
        return self

    @property
    def rules(self):
        if self._rules is None:
            r = subst([]) << empty
            if self.max_count is None:
                # We don't apply any semantic actions here
                # because this form is special-cased in :func:`_find_results`.
                # The ``group()`` is needed for that optimization, too.
                r = r | self * group(self.inner)
            elif self.max_count > 1:
                next_ = RepeatedNonterminal(max_count=self.max_count - 1,
                                            inner=self.inner)
                r = r | _continue_right_list << self.inner * next_
            else:
                r = r | _begin_list << self.inner
            self._rules = r.rules
        return self._rules

    def build_regex(self):
        if self.max_count is None:
            return self.inner.as_regex() + b'*'
        else:       # pragma: no cover
            return self.inner.as_regex() + (b'{0,%d}' % self.max_count)


class Rule(object):

    """A rule according to which a nonterminal can be parsed.

    Consists of a tuple of symbols (terminals or nonterminals)
    + a semantic action that will be applied to the tuple of results
    to produce this rule's final result.
    """

    def __init__(self, symbols, action=None):
        self.symbols = symbols
        self.action = action

        # This small hack allows us to check if an Earley item is completed
        # with a single tuple lookup, without a bounds check.
        # This speeds up parsing a bit.
        self.xsymbols = self.symbols + (None,)

    def __repr__(self):
        return '<Rule %r>' % (self.symbols,)

    def concat(self, other):
        if self.action is None and other.action is None:
            concat_action = None
        else:
            len1 = len(self.symbols)
            action1 = self.action
            action2 = other.action
            def concat_action(complain, nodes):
                nodes1 = nodes[:len1]
                if action1 is not None:
                    nodes1 = action1(complain, nodes1)
                nodes2 = nodes[len1:]
                if action2 is not None:
                    nodes2 = action2(complain, nodes2)
                return nodes1 + nodes2
        return Rule(self.symbols + other.symbols, concat_action)

    def wrap(self, func):
        inner_action = self.action
        def wrapper_action(complain, nodes):
            if inner_action is not None:
                nodes = inner_action(complain, nodes)
            nodes = tuple(node for node in nodes if node is not _SKIP)
            if getattr(func, 'with_complaints', False):
                r = func(complain, *nodes)
            else:
                r = func(*nodes)
            if r is _SKIP:
                return ()
            else:
                return (r,)
        return Rule(self.symbols, wrapper_action)


empty = SimpleNonterminal(name=u'empty', rules=[Rule(())], is_ephemeral=True)


def octet_range(min_, max_):
    """Create a terminal that accepts bytes from `min_` to `max_` inclusive."""
    bits = BitArray(256)
    for i in range(min_, max_ + 1):
        bits[i] = True
    return Terminal(bits=Bits(bits))

def octet(value):
    """Create a terminal that accepts only the `value` byte."""
    return octet_range(value, value)

def literal(s, case_sensitive=False):
    """Create a symbol that parses the `s` string."""
    if len(s) == 1:
        if case_sensitive:
            return octet(ord(s))
        else:
            return octet(ord(s.lower())) | octet(ord(s.upper()))
    else:
        r = empty
        for c in s:
            r = r * literal(c, case_sensitive)
        return _join_args << r

def as_symbol(x):
    return x if isinstance(x, Symbol) else literal(x)


recursive = SimpleNonterminal


class _Skip(object):

    def __repr__(self):
        return '_SKIP'

_SKIP = _Skip()

def skip(x):
    return _skip_args << as_symbol(x)

def group(x):
    return as_symbol(x).group()

def mark(symbol):
    """Wrap the symbol's result in a tuple where the first element is `symbol`.

    Used where the information about "which branch of the grammar was used"
    must be propagated upwards for further checks.
    """
    def mark_action(x):
        return (symbol, x)
    return mark_action << symbol


def maybe(inner, default=None):
    return inner | subst(default) << empty

def maybe_str(inner):
    return maybe(inner, u'')


def times(min_, max_, inner):
    inner = as_symbol(inner)
    if min_ == 0:
        return RepeatedNonterminal(max_count=max_, inner=inner)
    else:
        min_rule = empty
        for _ in range(min_):
            min_rule = min_rule * group(inner)
        min_rule = _as_list << min_rule
        if max_ == min_:
            return min_rule
        else:
            rest_rule = RepeatedNonterminal(max_count=(None if max_ is None
                                                       else max_ - min_),
                                            inner=inner)
            return min_rule + rest_rule

def string_times(min_, max_, inner):
    return u''.join << times(min_, max_, inner)

def many(inner):
    return times(0, None, inner)

def string(inner):
    return u''.join << many(inner)

def many1(inner):
    return times(1, None, inner)

def string1(inner):
    return u''.join << many1(inner)


def string_excluding(terminal, excluding):
    """
    ``string_excluding(t, ['foo', 'bar'])`` is the same as ``string(t)``,
    except it **never parses** the input strings
    "foo" and "bar" (case-insensitive).

    This is used where the grammar special-cases certain strings.
    For example, consider the ``link-param`` rule from RFC 5988.
    Strictly speaking, that rule matches the string::

      hreflang="Hello world!"

    because the ``link-extension`` rule matches it.
    But the spec obviously intends that
    an "hreflang" parameter must only have a language tag as a value,
    as it is special-cased in the definition of ``link-param``.
    Therefore, in our code for ``link-extension``,
    we exclude "hreflang" and other special cases
    from the allowed values of ``parmname``.

    This only works when the excluded strings are relatively few and short.
    """
    initials = set(s[0:1].lower() for s in excluding if s)

    free = terminal
    for c in initials:
        free = free - literal(c)

    r = free + string(terminal)
    for c in initials:
        continuations = [s[1:] for s in excluding if s and s[0:1].lower() == c]
        r = r | literal(c) + string_excluding(terminal, continuations)
    if '' not in excluding:
        r = r | subst(u'') << empty
    return r


class _AutoName(object):

    def __repr__(self):
        return '_AUTO'

_AUTO = _AutoName()


def named(name, citation=None, is_pivot=False):
    return (name, citation, is_pivot)

auto = named(_AUTO)
pivot = named(_AUTO, is_pivot=True)

def fill_names(scope, citation):
    """Process automatic names for all symbols in `scope`.

    When we write::

      foobar = literal(b'foo') | literal(b'bar')

    there is no way for `foobar` to know its own name
    (which is ``foobar``, important for error reporting),
    unless we post-process it with this function.
    It takes names from `scope` and writes them back into the symbols.
    This only happens for symbols sealed with :func:`auto` or :func:`pivot`.
    """
    for name, x in scope.items():
        if isinstance(x, Symbol) and x.name is _AUTO:
            x.name = name.rstrip('_').replace('_', '-')
            x.citation = citation


###############################################################################
# Functions that are useful as semantic actions in parsing rules.

def _skip_args(*_):
    return _SKIP

def _join_args(*args):
    return u''.join(args)

def subst(r):
    def substitute(*_):
        return r
    return substitute

def _as_list(*args):
    return list(args)

def _begin_list(*args):
    return [args if len(args) > 1 else args[0]]

def _continue_right_list(*args):
    list_ = args[-1]
    new_elem = args[:-1] if len(args) > 2 else args[0]
    return [new_elem] + list_

def can_complain(func):
    """Marks `func` (in-place) as capable of reporting notices.

    If so marked, `func` will be called
    with a special `complain` function as the first argument,
    which must be called to report a notice.
    """
    func.with_complaints = True
    return func


###############################################################################
# The input stream and parse error abstractions.

class Stream(object):

    # pylint: disable=attribute-defined-outside-init

    """Wraps a string of bytes that are the input to parsers.

    This class is directly used in :mod:`httpolice.framing1`,
    and it encapsulates some state that is passed around there,
    including complaints that are later "dumped" into the parsed message.
    In most other cases, you probably want :func:`simple_parse` instead.
    """

    _cache = OrderedDict()

    # Obtained by running under ``/usr/bin/time -v`` on a large tcpflow input
    # and increasing until the results stopped improving.
    _cache_size = 200

    def __init__(self, data, name=None):
        self.data = data
        self.name = name
        self._sane = True
        self._set_state((0, [], []))
        self._stack = []

    def _get_state(self):
        return (self.point, self.complaints[:], self.annotations[:])

    def _set_state(self, state):
        (self.point, self.complaints, self.annotations) = state

    def _is_empty_state(self):
        return self.point == 0 and not self.complaints and not self.annotations

    def __enter__(self):
        self._stack.append(self._get_state())
        return self

    def __exit__(self, exc_type, _1, _2):
        state = self._stack.pop()
        if exc_type is not None:
            self._set_state(state)
        return False

    def peek(self, n):
        return self.data[self.point:(self.point + n)]

    def __getitem__(self, i):
        if 0 <= i < len(self.data) - self.point:
            return self.data[(self.point + i):(self.point + i + 1)]
        elif i == len(self.data) - self.point:
            return b''
        else:   # pragma: no cover
            raise IndexError(i)

    @property
    def eof(self):
        return self.point == len(self.data)

    @property
    def sane(self):
        return self._sane and not self.eof

    @sane.setter
    def sane(self, value):
        self._sane = value

    def skip(self, n):
        self.point = min(self.point + n, len(self.data))

    def consume_n_bytes(self, n):
        r = self.peek(n)
        if len(r) < n:
            raise ParseError(name=self.name, point=self.point,
                             found=u'%d bytes' % len(r),
                             expected=[(u'%d bytes' % n,)])
        else:
            self.point += n
            return r

    def consume_rest(self):
        r = self.data[self.point:]
        self.point = len(self.data)
        return r

    def consume_regex(self, target, name=None):
        if isinstance(target, Symbol):
            regex = target.as_compiled_regex()
        else:
            regex = re.compile(target)
        match = regex.match(self.data, self.point)
        if match is None:
            raise ParseError(
                self.name, self.point, found=None,
                expected=[(target if name is None else name, None)])
        else:
            r = match.group(0)
            self.skip(len(r))
            return r.decode('iso-8859-1')

    def maybe_consume_regex(self, target):
        try:
            return self.consume_regex(target)
        except ParseError:
            return None

    def parse(self, target, to_eof=False, annotate_classes=None):
        annotate_classes = tuple(annotate_classes or ())
        key = None
        if self._is_empty_state() and to_eof:
            # Memoization is really only useful
            # when we're parsing something small in its entirety,
            # like a header value.
            # The above ``if`` means that the cache won't get in our way
            # when we're parsing something big in chunks,
            # like HTTP/1.x framing.
            key = (self.data, target, annotate_classes)
            item = self._cache.pop(key, None)
            if item is not None:
                (r, state) = item
                self._set_state(state)
                self._cache[key] = item
                return r

        r = parse(self, target.as_nonterminal(), to_eof, annotate_classes)
        if key is not None:
            self._cache[key] = (r, self._get_state())
            while len(self._cache) > self._cache_size:
                self._cache.popitem()
        return r

    def complain(self, notice_id, **context):
        self.complaints.append((notice_id, context))

    def add_complaints(self, complaints):
        self.complaints.extend(complaints)

    def dump_complaints(self, complain_func, **extra_context):
        for (notice_id, context) in self.complaints:
            context = dict(extra_context, **context)
            complain_func(notice_id, **context)
        self.complaints = []

    def add_annotations(self, annotations):
        self.annotations.extend(annotations)

    def collect_annotations(self):
        r = []
        i = 0
        for (start, end, obj) in self.annotations:
            if start >= i:
                r.append(self.data[i:start])
                r.append(obj)
                i = end
        r.append(self.data[i:])
        return [chunk for chunk in r if chunk != b'']


class ParseError(Exception):

    def __init__(self, name, point, found, expected):
        super(ParseError, self).__init__(u'unexpected %r at byte position %r' %
                                         (found, point))
        self.name = name
        self.point = point
        self.found = found
        self.expected = expected


###############################################################################
# The actual Earley parsing algorithms.
# These are written in a sort of low-level, non-idiomatic Python
# to make them less terribly inefficient.
# To compensate for this, they are heavily commented.


def _add_item(items, items_idx, items_set, symbol, rule, pos, start):
    # `items`, `items_idx` and `items_set` together constitute
    # an inventory of Earley items at a certain position of the input.
    # ``(symbol, rule, pos, start)`` is the item we want to append to it,
    # unless it's already present there.

    # `items` is the master list that is used for iterating over all items.
    # `items_idx` is an index of items by their *next symbols*,
    # which speeds up some frequent lookups.
    # `items_set` is the set of all items,
    # which speeds up checking for presence of an item before adding it.

    # In fact, `items_set` stores "fingerprints" of items, not actual items.
    # This makes it faster, as object equality is reduced to integer equality.
    fingerprint = (id(symbol), id(rule), pos, start)

    if fingerprint not in items_set:
        items_set.add(fingerprint)
        items.append((symbol, rule, pos, start))
        items_idx.setdefault(rule.xsymbols[pos], []).append(
            (symbol, rule, pos, start))


def parse(stream, target_symbol, to_eof=False, annotate_classes=()):
    (items, items_idx, items_set) = ([], {}, set())

    # Seed the initial items inventory with rules for `target_symbol`.
    chart = [(items, items_idx, items_set)]
    for rule in target_symbol.rules:
        _add_item(items, items_idx, items_set, target_symbol, rule, 0, 0)

    # Outer loop: over `data`.
    i = 0                  # Relative position in the stream.
    last_good_i = None     # `i` of the last complete parse of `target_symbol`.
    while True:
        token = stream[i]

        # Initialize the items inventory for the next `i`,
        # because we will be adding to it on successful scans.
        chart.append(([], {}, set()))

        # Load the items inventory for the current `i`.
        (items, items_idx, items_set) = chart[i]
        if len(items) == 0:
            # This means that there were no successful scans at previous `i`.
            break

        # Inner loop: over items at the current `i`.
        j = 0
        while True:
            (symbol, rule, pos, start) = items[j]
            next_symbol = rule.xsymbols[pos]

            if next_symbol is None:
                # This is a completed item.
                if symbol is target_symbol:
                    # Remember as a valid parse.
                    last_good_i = i
                # Earley completion:
                # copy items from this rule's start `i` to the current `i`,
                # advancing their rules by 1 position.
                (_, items_idx1, _) = chart[start]
                candidates = items_idx1.get(symbol, [])
                for (symbol1, rule1, pos1, start1) in candidates:
                    _add_item(items, items_idx, items_set,
                              symbol1, rule1, pos1 + 1, start1)

            elif isinstance(next_symbol, Nonterminal):
                # Skip over nullable symbols. See:
                # http://loup-vaillant.fr/tutorials/earley-parsing/empty-rules
                if next_symbol.is_nullable():
                    _add_item(items, items_idx, items_set,
                              symbol, rule, pos + 1, start)
                # Earley prediction:
                # add rules for `next_symbol` to the current `i`.
                for next_rule in next_symbol.rules:
                    _add_item(items, items_idx, items_set,
                              next_symbol, next_rule, 0, i)

            else:
                # `next_symbol` is a `Terminal`.
                # Earley scan:
                # copy this item to the next `i`,
                # advancing its rule by 1 position.
                if token and next_symbol.match(token):
                    (items1, items_idx1, items_set1) = chart[i + 1]
                    _add_item(items1, items_idx1, items_set1,
                              symbol, rule, pos + 1, start)

            j += 1
            if j == len(items):
                break

        if not token:        # End of stream.
            break
        i += 1

    if (last_good_i is not None) and (last_good_i == i or not to_eof):
        results = _find_results(stream, target_symbol, chart, last_good_i,
                                [], annotate_classes)
        for start_i, _, result, complaints, annotations in results:
            # There may be multiple valid parses in case of ambiguities,
            # but in practice we just want
            # the first parse that stretches to the beginning of the input.
            if start_i == 0:
                stream.skip(last_good_i)
                stream.add_complaints(complaints)
                stream.add_annotations(annotations)
                return result

    raise _build_parse_error(stream, target_symbol, chart)


def _find_results(stream, symbol, chart, end_i,
                  outer_parents, annotate_classes):
    # The trivial base case is to find the parse result of a terminal.
    if isinstance(symbol, Terminal):
        if end_i > 0:
            token = stream[end_i - 1]
            if symbol.match(token):
                token = token.decode('iso-8859-1')
                yield end_i - 1, None, token, [], []
        return

    # With that out of the way, the interesting story is nonterminals.

    # Iterate over all completed items for this nonterminal at this `i`.
    (_, items_idx, _) = chart[end_i]
    for item in items_idx.get(None, []):
        (sym, rule, _, start_i) = item
        if sym is not symbol:
            continue

        # We don't want to consider items that are
        # already being processed further up the stack.
        # Otherwise, we would fall into unbounded recursion.
        if item in outer_parents:
            continue

        # Now we recursively collect the results
        # for each symbol of this rule, starting from the end.
        # There may be multiple completed items for each symbol,
        # but we need to find a combination that "fits together":
        # every next item starts where the previous item ends.

        # This process can more elegantly be coded as
        # two mutually recursive functions (see
        # https://github.com/tomerfiliba/tau/blob/ebefd88/earley3.py#L145
        # for an example),
        # but that hits maximum recursion depth too soon.
        # Instead, we roll our own "stack" composed of "frames".
        # Every frame corresponds to one position (symbol) in the rule.
        # We start with one empty frame.
        frames = [(end_i, outer_parents + [item], None, None, None, None)]

        # We have to special-case `RepeatedNonterminal` because
        # it can produce long strings that exceed maximum recursion depth
        # (for example, request URIs with even moderately long query strings).
        # We unroll its left recursion, producing one frame *per repetition*.
        if isinstance(symbol, RepeatedNonterminal) and \
                rule.xsymbols[0] is symbol:
            n_nodes = None
            inner_symbol = rule.symbols[-1]
        else:
            n_nodes = len(rule.symbols)

        while True:
            (i, parents, rs, node, complaints, annotations) = frames.pop()
            if len(frames) == n_nodes:
                # We found a complete parse for this rule.
                # It starts at `i`. Is that what we expected?
                if i != start_i:
                    # We'll just keep trying other combinations.
                    continue

                # Great. We have the raw results for each inner symbol.
                # Now we need to do some post-processing.
                # First, we collect the complaints and annotations
                # that were produced when parsing these symbols.
                nodes = []
                all_complaints = []
                all_annotations = []
                for (_, _, _, n, coms, anns) in reversed(frames):
                    nodes.append(n)
                    all_complaints.extend(coms)
                    all_annotations.extend(anns)

                # Then we invoke the rule's semantic action,
                # which determines the final form of the parse result.
                # It can also add its own complaints.
                if rule.action is not None:
                    def complain(id_, **ctx):
                        # pylint: disable=cell-var-from-loop
                        all_complaints.append((id_, ctx))
                    nodes = rule.action(complain, tuple(nodes))
                nodes = tuple(n for n in nodes if n is not _SKIP)
                if len(nodes) == 0:
                    result = _SKIP
                elif len(nodes) == 1:
                    result = nodes[0]
                else:
                    result = nodes

                # Finally, annotate if needed.
                if isinstance(result, annotate_classes):
                    all_annotations.append((start_i, end_i, result))

                # And that's one complete parse for `target_symbol`
                # ending at `end_i`.
                yield start_i, item, result, all_complaints, all_annotations

                if len(frames) == 0:
                    break

            else:
                # We haven't covered the entire rule yet. Keep working.
                # Handle the symbol at the current position of the rule.
                if rs is None:
                    if n_nodes is not None:
                        inner_symbol = rule.symbols[-len(frames) - 1]
                    # Recursively get an iterator
                    # over possible results for this symbol.
                    rs = _find_results(stream, inner_symbol, chart, i, parents,
                                       annotate_classes)

                # Get the next result for this symbol.
                r = next(rs, None)
                if r is None:
                    # None left, so we must fall back (to ``pos + 1``)
                    # and try other results for the previous symbol.
                    if len(frames) > 0:
                        continue
                    else:
                        # If there are no previous symbols,
                        # then there are no more parses for this `item`.
                        break

                new_i, new_item, new_node, new_complaints, new_annotations = r

                if new_i < i:
                    # We moved one or more token to the left in the input data,
                    # so there's no more danger of unbounded recursion.
                    new_parents = []
                elif n_nodes is None:
                    # No input data was consumed, so we stayed at the same `i`.
                    # Because we are unrolling recursion into iteration,
                    # we must avoid this Earley item on our next iteration,
                    # otherwise we will be stuck at the same place forever.
                    new_parents = parents + [new_item]
                else:
                    # No input data was consumed, so we stayed at the same `i`.
                    # But "unbounded iteration" won't happen here
                    # because we are limited to `n_nodes`.
                    new_parents = parents

                if n_nodes is None and new_i == start_i:
                    # We found a valid parse for this `RepeatedNonterminal`.
                    # Assemble the results like in the general case above,
                    # only we don't need to apply any semantic actions.
                    nodes = [new_node]
                    all_complaints = new_complaints[:]
                    all_annotations = new_annotations[:]
                    for (_, _, _, n, coms, anns) in reversed(frames):
                        nodes.append(n)
                        all_complaints.extend(coms)
                        all_annotations.extend(anns)
                    yield new_i, item, nodes, all_complaints, all_annotations

                if new_i >= start_i:
                    # Store the result on our stack.
                    # Also store the iterator,
                    # so we can come back to it and get further results.
                    frames.append((i, parents, rs, new_node,
                                   new_complaints, new_annotations))
                    # Proceed to the next symbol (at ``pos - 1``)
                    # and try to find a result for that, ending at `new_i`.
                    frames.append((new_i, new_parents, None, None, None, None))
                else:
                    # This result gets us too far back in the input data.
                    # But we will try other results from this iterator.
                    frames.append((i, parents, rs, node,
                                   complaints, annotations))


def _build_parse_error(stream, target_symbol, chart):
    # Find the last `i` that had some Earley items --
    # that is, the last `i` where we could still make sense of the input data.
    i, items = [(i, items)
                for (i, (items, _, _)) in enumerate(chart)
                if len(items) > 0][-1]
    found = stream[i]

    # What terminal symbols did we expect at that `i`?
    expected = OrderedDict()
    for (symbol, rule, pos, start) in items:
        next_symbol = rule.xsymbols[pos]
        if isinstance(next_symbol, Terminal):
            chars = format_chars(next_symbol.chars())
            # And why did we expect it? As part of what nonterminals?
            expected.setdefault(chars, set()).update(
                _find_pivots(chart, symbol, start))

        if symbol is target_symbol and next_symbol is None:
            # This item indicates a complete parse of `target_symbol`,
            # so if the input data just stopped there, that would work, too,
            expected[u'end of data'] = None

    return ParseError(stream.name, stream.point + i,
                      found, list(expected.items()))


def _find_pivots(chart, symbol, start, stack=None):
    if symbol.is_pivot:
        yield symbol
    else:
        stack = (stack or []) + [(symbol, start)]
        (_, items_idx, _) = chart[start]
        parents = items_idx.get(symbol, [])
        for (parent, _, _, parent_start) in parents:
            if (parent, parent_start) not in stack:
                for p in _find_pivots(chart, parent, parent_start, stack):
                    yield p


###############################################################################
# Miscellaneous helpers.

def simple_parse(data, symbol, complain, fail_notice_id, annotate_classes=None,
                 **extra_context):
    """(Try to) parse an entire string as a single grammar symbol.

    This wraps :class:`Stream` in a simpler interface for the common case.
    """
    if not isinstance(data, bytes):
        try:
            data = data.encode('iso-8859-1')
        except UnicodeError as e:
            complain(fail_notice_id, error=e, **extra_context)
            r = Unavailable
            return r if annotate_classes is None else (r, None)

    stream = Stream(data)

    try:
        r = stream.parse(symbol, to_eof=True,
                         annotate_classes=annotate_classes)
    except ParseError as e:
        complain(fail_notice_id, error=e, **extra_context)
        r = Unavailable
    else:
        stream.dump_complaints(complain, **extra_context)

    if annotate_classes is None:
        return r
    else:
        return (r, stream.collect_annotations())
