# -*- coding: utf-8; -*-

"""Wrappers over raw HTTP headers.

HTTPolice works with headers on two levels.

On the low level, :class:`httpolice.structure.HeaderEntry`
is a single name-value line from a message's headers (or trailers).

On a higher level, :class:`HeaderView` and its subclasses
aggregate, parse, and represent various header entries.
They know how to combine two entries with the same name into one entry.
They know how to parse their contents.
And to simplify the checks code, they provide some **magic**.
Particularly non-obvious are comparisons of :class:`HeaderView` (q.v.).
"""

import copy
import operator
import sys

from httpolice import known
from httpolice.known import HeaderRule, h
from httpolice.parse import parse
from httpolice.structure import Parametrized, Unavailable, okay
from httpolice.syntax.rfc7230 import quoted_string, token
from httpolice.util.data import duplicates


class HeadersView(object):

    """Wraps all headers of a single message, exposing them as attributes."""

    special_cases = {}

    @classmethod
    def special_case(cls, view_cls):
        assert view_cls.name not in cls.special_cases
        cls.special_cases[view_cls.name] = view_cls
        return view_cls
        
    def __init__(self, message):
        self._message = message
        self._cache = {}

    def __getattr__(self, name):
        return self[getattr(h, name)]

    def __getitem__(self, key):
        if key not in self._cache:
            rule = known.header.rule_for(key)

            # Some headers have more internal structure than can be handled
            # by a simple context-free parser, so they need special-casing.
            # For the rest, we only need to know a generic "rule" for combining
            # multiple entries (and a parser to parse the value).
            if key in self.special_cases:
                assert rule is HeaderRule.special
                cls = self.special_cases[key]
            else:
                assert rule is not HeaderRule.special
                if rule is HeaderRule.single:
                    cls = SingleHeaderView
                elif rule is HeaderRule.multi:
                    cls = MultiHeaderView
                else:
                    cls = UnknownHeaderView

            self._cache[key] = cls(self._message, key)

        return self._cache[key]

    @property
    def names(self):
        seen = set()
        for entries in [self._message.header_entries,
                        self._message.trailer_entries]:
            for entry in entries:
                if entry.name not in seen:
                    yield entry.name
                    seen.add(entry.name)

    def __iter__(self):
        for name in self.names:
            yield self[name]

    def enumerate(self, name=None):
        return [
            (from_trailer, i, entry)
            for from_trailer, entries
            in [(False, self._message.header_entries),
                (True, self._message.trailer_entries)]
            for i, entry in enumerate(entries or [])
            if (name is None) or (name == entry.name)
        ]

    def clearly(self, predicate):
        return set(name for name in self.names if predicate(name))


class HeaderView(object):

    """Wraps all headers with a particular name in a given message.

    This class has **tricky comparison magic** to simplify checks.
    All comparisons return `False` when the value is not :func:`okay`
    (is absent or malformed).
    Thus, the following expression::

      msg.headers.last_modified <= date(2016, 4, 29)

    is **not the same** as::

      not (msg.headers.last_modified > date(2016, 4, 29))

    """

    def __init__(self, message, name):
        self.message = message
        self.name = name
        self._entries = self._value = None

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)

    def _process_parsed(self, entry, parsed):
        # pylint: disable=unused-argument
        return parsed

    def _pre_parse(self):
        entries = []
        values = []
        items = self.message.headers.enumerate(self.name)
        syntax = known.header.syntax_for(self.name)
        for from_trailer, i, entry in items:
            if from_trailer and known.header.is_bad_for_trailer(self.name):
                self.message.complain(1026, entry=entry)
                continue
            entries.append(entry)
            if syntax is None:
                parsed = entry.value
            else:
                (parsed, annotations) = parse(
                    entry.value, syntax,
                    self.message.complain, 1000, place=entry,
                    annotate_classes=known.classes)
                if not isinstance(parsed, Unavailable):
                    parsed = self._process_parsed(entry, parsed)
                    self.message.annotations[(from_trailer, i)] = annotations
            values.append(parsed)
        return entries, values

    def _parse(self):
        raise NotImplementedError()

    @property
    def total_entries(self):
        return len(self.message.headers.enumerate(self.name))

    @property
    def entries(self):
        if self._entries is None:   # pragma: no cover
            self._parse()
        return self._entries

    @property
    def value(self):
        if self._entries is None:
            self._parse()
        return self._value

    @property
    def is_present(self):
        if self._entries is None:
            self._parse()
        return len(self._entries) > 0

    @property
    def is_absent(self):
        return not self.is_present

    @property
    def is_okay(self):
        return okay(self.value)

    def __bool__(self):
        return bool(self.value)

    if sys.version_info[0] < 3:     # pragma: no cover
        __nonzero__ = __bool__

    def __iter__(self):
        return iter(self.value)

    def __contains__(self, other):
        # Since headers often contain `Parametrized` values,
        # it's useful to be able to check membership by the item itself,
        # ignoring its parameters.
        # This is handled by :meth:`Parametrized.__eq__`,
        # but it's only invoked when the `Parametrized` is on the left side.
        # pylint: disable=not-an-iterable
        return any(val == other for val in self)

    def _compare(self, other, op):
        # It would be nice to be able to compare headers by values, as in::
        #
        #   resp.headers.last_modified == req.headers.if_modified_since
        #
        # Unfortunately, there are places
        # (such as :meth:`httpolice.blackboard.Blackboard.complain`)
        # where we need header-to-header equality to be less magical.
        # And if we can't do this magic for equality,
        # there's no sense in doing it for other operations.
        # So we just say that comparing headers to headers is `NotImplemented`
        # (fall back to comparing their object identities).
        #
        # Now, the following form still works::
        #
        #   resp.headers.last_modified == req.headers.if_modified_since.value
        #
        # so we don't lose all that much.

        if isinstance(other, HeaderView):
            return NotImplemented
        else:
            return self.is_okay and okay(other) and op(self.value, other)

    def __lt__(self, other):
        return self._compare(other, operator.lt)

    def __le__(self, other):
        return self._compare(other, operator.le)    # pragma: no cover

    def __eq__(self, other):
        return self._compare(other, operator.eq)

    def __ne__(self, other):
        return self._compare(other, operator.ne)

    def __ge__(self, other):
        return self._compare(other, operator.ge)

    def __gt__(self, other):
        return self._compare(other, operator.gt)

    __hash__ = None

    def __getattr__(self, name):
        return getattr(self.value, name)


class UnknownHeaderView(HeaderView):

    """Wraps a generic header that we know nothing about."""

    def _parse(self):
        # RFC 7230 section 3.2.2 permits combining field-values with a comma
        # even if we don't really know what the header is.
        entries, values = self._pre_parse()
        self._value = b','.join(values) if values else None
        self._entries = entries


class SingleHeaderView(HeaderView):

    """Wraps a header that can only appear once in a message."""

    def _parse(self):
        entries, values = self._pre_parse()
        if entries:
            if len(entries) > 1:
                self.message.complain(1013, header=self, entries=entries)
            self._value = values[-1]
            self._entries = [entries[-1]]
        else:
            self._value = None
            self._entries = []


class MultiHeaderView(HeaderView):

    """Wraps a header that can appear multiple times in a message."""

    def _parse(self):
        entries, values = self._pre_parse()
        # Some headers, such as ``Vary``, permit both a comma-separated list
        # (which can be spread over multiple entries) as well as a singular
        # value (which cannot be combined with any other).
        singular = [v for v in values
                    if not isinstance(v, (list, Unavailable))]
        if singular:
            if len(singular) == len(entries) == 1:
                self._value = singular[0]
            else:
                self._value = [Unavailable()]
                self.message.complain(1013, header=self, entries=entries)
        else:
            self._value = []
            for v in values:
                if isinstance(v, Unavailable):
                    self._value.append(v)
                else:
                    self._value.extend(v)
        self._entries = entries

    def __iter__(self):
        # pylint: disable=not-an-iterable
        return iter(v for v in self.value if okay(v))


class ArgumentsView(HeaderView):           # pylint: disable=abstract-method

    """
    For a header whose parsed value contains some sort of ``name[=argument]``
    pairs, and the argument needs to be parsed depending on the name.
    """

    knowledge = None

    def _process_parsed(self, entry, parsed):
        return [self._process_pair(entry, d) for d in parsed]

    def _process_pair(self, entry, pair):
        name, argument = pair
        if argument is None:
            if self.knowledge.argument_required(name):
                self.message.complain(1156, entry=entry, name=name)
                argument = Unavailable(u'')
        else:
            syntax = self.knowledge.syntax_for(name)
            if self.knowledge.no_argument(name):
                self.message.complain(1157, entry=entry, name=name)
                argument = Unavailable(argument)
            elif syntax is not None:
                argument = parse(argument, syntax,
                                 self.message.complain, 1158, place=entry,
                                 name=name, value=argument)
        return Parametrized(name, argument)


class DirectivesView(ArgumentsView):        # pylint: disable=abstract-method

    """For a header whose value is a list of ``directive[=argument]`` pairs."""

    def __getattr__(self, name):
        return self[getattr(self.knowledge.accessor, name)]

    def __getitem__(self, key):
        for directive, argument in self:
            if directive == key:
                return True if argument is None else argument
        return None


@HeadersView.special_case
class CacheControlView(DirectivesView, MultiHeaderView):

    name = h.cache_control
    knowledge = known.cache_directive

    def _process_pair(self, entry, pair):
        (directive, argument) = pair
        if argument is not None:
            (symbol, argument) = argument

            if known.cache_directive.quoted_string_preferred(directive) and \
                    symbol is not quoted_string:
                self.message.complain(1154, directive=directive)

            if known.cache_directive.token_preferred(directive) and \
                    symbol is not token:
                self.message.complain(1155, directive=directive)

        return super(CacheControlView, self). \
            _process_pair(entry, (directive, argument))


@HeadersView.special_case
class StrictTransportSecurityView(DirectivesView, SingleHeaderView):

    name = h.strict_transport_security
    knowledge = known.hsts_directive


@HeadersView.special_case
class AltSvcView(ArgumentsView, MultiHeaderView):

    name = h.alt_svc
    knowledge = known.alt_svc_param

    def _process_parsed(self, entry, parsed):
        if parsed == u'clear':
            return parsed

        # Parse every parameter's value according to its defined parser.
        parsed = copy.deepcopy(parsed)
        for alternative in parsed:
            alternative.param.sequence[:] = super(AltSvcView, self). \
                _process_parsed(entry, alternative.param.sequence)
        return parsed


@HeadersView.special_case
class PreferView(DirectivesView, MultiHeaderView):

    name = h.prefer
    knowledge = known.preference

    # Each preference has two level of wrapping: ``((name, value), params)``.
    # Params are currently not used for anything, so we peel them off
    # (but they are still part of ``self.value``).

    def _process_parsed(self, entry, parsed):
        return [Parametrized(self._process_pair(entry, pair), params)
                for (pair, params) in parsed]

    def __getitem__(self, key):
        for (preference, value) in self.without_params:
            if preference == key:
                return True if value is None else value
        return None

    @property
    def without_params(self):
        return [pref for (pref, _) in self]


@HeadersView.special_case
class PreferenceAppliedView(DirectivesView, MultiHeaderView):

    name = h.preference_applied
    knowledge = known.preference


@HeadersView.special_case
class ForwardedView(ArgumentsView, MultiHeaderView):

    name = h.forwarded
    knowledge = known.forwarded_param

    def _process_parsed(self, entry, parsed):
        # Work at the second level of nesting (forwarded-pairs,
        # not forwarded-elements).
        elements = [super(ForwardedView, self)._process_parsed(entry, elem)
                    for elem in parsed]

        # ``Forwarded`` is probably more likely than other headers to appear
        # multiple times in a message (as appended by intermediaries), so
        # it's more important to report these notices on a specific entry
        # rather than on the entire `ForwardedView` in `check_request`.
        for elem in elements:
            for duped in duplicates(param for (param, _value) in elem):
                self.message.complain(1296, entry=entry, param=duped)
        if len(elements) > 1 and all(len(elem) == 1 for elem in elements):
            if not duplicates(param for [(param, _value)] in elements):
                self.message.complain(1297, entry=entry,
                                      n_elements=len(elements))

        return elements
