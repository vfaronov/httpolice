# -*- coding: utf-8; -*-

"""A library of parser combinators based on the Earley algorithm.

This is used mainly for parsing header values (see :mod:`httpolice.header`).
The grammar defined with these combinators is in :mod:`httpolice.syntax`.

We use Earley -- instead of more mainstream approaches like LR(1) -- because
Earley can deal with any (context-free) grammar. So we can use the rules almost
exactly as defined in the RFCs. We don't need to transform them, add lookaheads
and such; they just work. And we get precise, detailed error messages.

The grammar given in the RFCs has octets as terminal symbols, and we follow it.
This means we have to run Earley on individual bytes rather than higher-level
tokens, which makes it slow. To compensate, we memoize, which is easy to do
for things like headers. For HTTP/1.x message framing, however, we don't even
bother with Earley: instead we use simple line-oriented rules hardcoded
in :mod:`httpolice.framing1`.

Parsed bytestrings are automatically decoded from ISO-8859-1 -- the historic
encoding of HTTP. After that, the grammar's semantic actions are applied
(as specified with the ``<<`` operator, :meth:`Symbol.__rlshift__`).
The semantic actions convert parsed strings into objects that are more
suitable for further work -- mainly classes from :mod:`httpolice.structure`.

A semantic action can also produce complaints (notices), if it is decorated
with :func:`can_complain`. For example, this is how no. 1015 is implemented:
only the parser sees the ``BWS``, but its complaint is propagated up to
the message where the ``BWS`` was found.

Another side result of parsing is the input string *annotated* with instances
of parsed objects. For example, in ``Accept: text/xml;q=1.0``, the ``text/xml``
is parsed into a :class:`~httpolice.structure.MediaType` object. Thus,
the annotated string is::

    [MediaType(u'text/xml'), b';q=1.0']

This annotated representation is then used in :mod:`httpolice.reports.html`
to render ``text/xml`` as a link to the RFC, using :mod:`httpolice.known`.

"""

from collections import OrderedDict
import operator
from six.moves import range

from bitstring import BitArray, Bits
import six

from httpolice.structure import Unavailable
from httpolice.util.text import format_chars


###############################################################################
# The main interface to parsing.

def parse(data, symbol, complain=None, fail_notice_id=None,
          annotate_classes=None, **extra_context):
    """(Try to) parse a string as a grammar symbol.

    Uses memoization internally, so parsing the same strings many times isn't
    expensive.

    :param data:
        The bytestring or Unicode string to parse. Unicode will be encoded
        to ISO-8859-1 first; encoding failure is treated as a parse failure.
    :param symbol:
        The :class:`Symbol` to parse as.
    :param complain:
        If not `None`, this function will be called with any complaints
        produced while parsing (only if parsing was successful), like
        `Blackboard.complain`.
    :param fail_notice_id:
        If not `None`, failure to parse will be reported as this notice ID
        instead of raising `ParseError`. The complaint will have an ``error``
        key with the `ParseError` as value.
    :param annotate_classes:
        If not `None`, these classes will be annotated in the input `data`.

    Any `extra_context` will be passed to `complain` with every complaint.

    :return:
        If `annotate_classes` is `None`, then the result of parsing
        (`Unavailable` if parse failed). Otherwise, a pair: the same result +
        the annotated input string as a list of bytestrings and instances
        of `annotate_classes`.

    :raises:
        If `fail_notice_id` is `None`, raises :exc:`ParseError` on parse
        failure, or :exc:`UnicodeError` if `data` cannot be encoded to bytes.

    """
    annotate_classes = tuple(annotate_classes or ())        # for `isinstance`

    if not isinstance(data, bytes):
        try:
            data = data.encode('iso-8859-1')
        except UnicodeError as e:
            if fail_notice_id is None:      # pragma: no cover
                raise
            complain(fail_notice_id, error=e, **extra_context)
            r = Unavailable(data)
            return (r, None) if annotate_classes else r

    # Check if we have already memoized this.
    key = (data, symbol, annotate_classes)
    parse_result = _memo.pop(key, None)
    if parse_result is not None:
        _memo[key] = parse_result       # Reinsertion maintains LRU order.
    else:
        try:
            parse_result = _inner_parse(data, symbol.as_nonterminal(),
                                        annotate_classes)
        except ParseError as e:
            if fail_notice_id is None:
                raise
            complaint = (fail_notice_id, {'error': e})
            parse_result = (Unavailable(data), [complaint], [])
        else:
            _memo[key] = parse_result
            while len(_memo) > MEMO_LIMIT:
                _memo.popitem(last=False)

    (r, complaints, annotations) = parse_result
    if complain is not None:
        for (notice_id, context) in complaints:
            context = dict(extra_context, **context)
            complain(notice_id, **context)
    if annotate_classes:
        return (r, _splice_annotations(data, annotations))
    else:
        return r


_memo = OrderedDict()

MEMO_LIMIT = 500


def _splice_annotations(data, annotations):
    r = []
    i = 0
    for (start, end, obj) in annotations:
        if start >= i:
            r.append(data[i:start])
            r.append(obj)
            i = end
    r.append(data[i:])
    return [chunk for chunk in r if chunk != b'']


class ParseError(Exception):

    def __init__(self, name, position, expected, found=None):
        """
        :param name: Name of the input stream (file) with the error, or `None`.
        :param position: Byte offset at which the error was encountered.
        :param expected:
            List of ``(description, symbols)``, where `description` is
            a free-form description of what could satisfy parse at that
            `position` in the input, and `symbols` is an iterable
            of :class:`Symbol` as part of which this `description` would be
            expected. `description` may be `None` if an entire symbol was
            expected at that `position` and no further detail is available.
        :param found:
            A bytestring of length 1 or 0 (for EOF) that was found
            at `position`, or `None` if irrelevant.

        """
        super(ParseError, self).__init__(
            u'unexpected input at byte position %r' % position)
        self.name = name
        self.position = position
        self.expected = expected
        self.found = found


###############################################################################
# Combinators to construct a grammar suitable for the Earley algorithm.


class Symbol(object):

    """A symbol of the grammar (either terminal or nonterminal)."""

    def __init__(self, name=None, citation=None, is_pivot=False,
                 is_ephemeral=None):
        """
        :param name:
            The name of this symbol in the grammar, normally as specified
            in `citation`.
        :param citation:
            The :class:`~httpolice.citation.Citation` for the document that
            defines this symbol.
        :param is_pivot:
            `True` if this symbol is a meaningful enough block of the grammar
            to be shown to the user as part of a :exc:`ParseError` explanation
            (see :func:`_build_parse_error`).
        :param is_ephemeral:
            Whether this symbol is ephemeral. If `None`, this is determined
            heuristically. See :meth:`is_ephemeral`.

        """
        self.name = name
        self.citation = citation
        self.is_pivot = is_pivot
        self._is_ephemeral = is_ephemeral

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__,
                            self.name or hex(id(self)))

    def __gt__(self, seal):
        """``sym >seal`` seals the `sym` symbol, then applies `seal` to it.

        This causes the symbol to be treated as a unit, with a specific name
        and (usually) citation. It will then never be inlined into other
        symbol's rules. This leads to an almost exact correspondence between
        the layout of `Symbol` objects and the actual grammar given in RFCs.
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
        """Is it OK to inline this symbol into others (if possible)?

        Ephemeral symbols are a side effect of constructing a grammar using our
        combinators. For example, when we write::

            foo = bar | baz | qux           > auto

        we want `foo` to consist of three rules. But naturally Python
        interprets this as ``(bar | baz) | qux``, where ``bar | baz`` is
        an ephemeral symbol -- it needs to be "dissolved" in the rules
        for `foo`.

        """
        if self._is_ephemeral is None:
            return (self.name is None)
        else:
            return self._is_ephemeral

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
            # If a string is wrapped in a class, this often means that we want
            # to annotate this string. But for that to work, the string must be
            # the result of parsing an entire grammar symbol (that's how
            # `_find_results` works). So we need to prevent this symbol from
            # being inlined into others.
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

    """A terminal symbol of the grammar, matching some set of octets."""

    def __init__(self, name=None, citation=None, bits=None):
        super(Terminal, self).__init__(name, citation)
        self.bits = bits if bits is not None else Bits(256)

    def chars(self):
        return [six.int2byte(i) for (i, v) in enumerate(self.bits) if v]

    def match(self, char):
        return self.bits[ord(char)]

    def group(self):
        return self

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
        self._rules = rules or []

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

    rec = property(None, set_rules_from)        # used for recursive rules


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


class _Skip(object):

    def __repr__(self):
        return '_SKIP'

_SKIP = _Skip()


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
    except it **never parses** the input strings "foo" and "bar"
    (case-insensitive).

    This is used where the grammar special-cases certain strings. For example,
    consider RFC 5988. Strictly speaking, the string::

      hreflang="Hello world!"

    matches the ``link-param`` rule, because it matches ``link-extension``.
    But the spec obviously intends that an "hreflang" parameter must only have
    a language tag as a value, as it is special-cased in the definition
    of ``link-param``. Therefore, in our code for ``link-extension``, we
    exclude "hreflang" and other special cases from the allowed values
    of ``parmname``.

    This only works when the excluded strings are relatively few and short.

    """
    initials = set(s[0:1].lower() for s in excluding if s)

    free = terminal
    for c in initials:
        free = free - literal(c)

    r = free + string(terminal)
    for c in initials:
        continuations = [s[1:] for s in excluding if s[0:1].lower() == c]
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

      foobar = literal('foo') | literal('bar')

    there is no way for `foobar` to know its own name (which is ``foobar``,
    important for error reporting), unless we post-process it with this
    function. It takes names from `scope` and writes them back into
    the symbols. This only happens for symbols sealed with :func:`auto`
    or :func:`pivot`.
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


def _inner_parse(data, target_symbol, annotate_classes):
    length = len(data)
    (items, items_idx, items_set) = ([], {}, set())

    # Seed the initial items inventory with rules for `target_symbol`.
    chart = [(items, items_idx, items_set)]
    for rule in target_symbol.rules:
        _add_item(items, items_idx, items_set, target_symbol, rule, 0, 0)

    # Outer loop: over `data`.
    for i in range(length + 1):
        token = data[i : i + 1]

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

    # pylint: disable=undefined-loop-variable
    if i == length:             # Successfully parsed up to the end of stream.
        results = _find_results(data, target_symbol, chart, i,
                                [], annotate_classes)
        for start_i, _, result, complaints, annotations in results:
            # There may be multiple valid parses in case of ambiguities,
            # but in practice we just want
            # the first parse that stretches to the beginning of the input.
            if start_i == 0:
                return (result, complaints, annotations)

    raise _build_parse_error(data, target_symbol, chart)


def _find_results(data, symbol, chart, end_i,
                  outer_parents, annotate_classes):
    # The trivial base case is to find the parse result of a terminal.
    if isinstance(symbol, Terminal):
        if end_i > 0:
            token = data[end_i - 1 : end_i]
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
                    rs = _find_results(data, inner_symbol, chart, i, parents,
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


def _build_parse_error(data, target_symbol, chart):
    # Find the last `i` that had some Earley items --
    # that is, the last `i` where we could still make sense of the input data.
    i, items = [(i, items)
                for (i, (items, _, _)) in enumerate(chart)
                if len(items) > 0][-1]
    found = data[i : i + 1]

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

    return ParseError(name=None, position=i,
                      expected=list(expected.items()), found=found)


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
