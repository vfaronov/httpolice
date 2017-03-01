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
from httpolice.known import alt_svc_param, cache_directive, h, header
import httpolice.known.hsts_directive
from httpolice.parse import simple_parse
from httpolice.structure import Parametrized, Unavailable, okay
from httpolice.syntax.rfc7230 import quoted_string, token


class HeadersView(object):

    """Wraps all headers of a single message, exposing them as attributes."""

    def __init__(self, message):
        self._message = message
        self._cache = {}

    def __getattr__(self, key):
        return self[getattr(h, key)]

    def __getitem__(self, key):
        if key not in self._cache:
            rule = header.rule_for(key)

            # Some headers have more internal structure
            # than can be handled by a simple context-free parser,
            # so they need special-casing.
            if key == h.cache_control:
                cls = CacheControlView
            elif key == h.strict_transport_security:
                cls = StrictTransportSecurityView
            elif key == h.alt_svc:
                cls = AltSvcView
            elif key == h.prefer:
                cls = PreferView
            elif key == h.preference_applied:
                cls = PreferenceAppliedView

            # For the rest, we only need to know
            # a generic "rule" for combining multiple entries,
            # and a parser to parse the value.
            elif rule == header.SINGLE:
                cls = SingleHeaderView
            elif rule == header.MULTI:
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

    def _process_parsed(self, entry, value):
        # pylint: disable=unused-argument
        return value

    def _pre_parse(self):
        entries = []
        values = []
        items = self.message.headers.enumerate(self.name)
        parser = header.parser_for(self.name)
        for from_trailer, i, entry in items:
            if from_trailer and header.is_bad_for_trailer(self.name):
                self.message.complain(1026, entry=entry)
                continue
            entries.append(entry)
            if parser is None:
                parsed = entry.value
            else:
                (parsed, annotations) = simple_parse(
                    entry.value, parser,
                    self.message.complain, 1000, place=entry,
                    annotate_classes=known.classes)
                if parsed is not Unavailable:
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
        #   response.headers.etag == request.headers.if_match
        #
        # Unfortunately, there are places
        # (such as :meth:`httpolice.blackboard.Blackboard.complain`)
        # where we need header-to-header equality to be less magical
        # (see ``test/combined_data/1277_4.https``).
        # And if we can't do this magic for equality,
        # there's no sense in doing it for other operations.
        # So we just say that comparing headers to headers is `NotImplemented`
        # (fall back to comparing their object identities).
        #
        # Now, the following form still works::
        #
        #   response.headers.etag == request.headers.if_match.value
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
                self.message.complain(1013, header=self.name, entries=entries)
            self._value = values[-1]
            self._entries = [entries[-1]]
        else:
            self._value = None
            self._entries = []


class MultiHeaderView(HeaderView):

    """Wraps a header that can appear multiple times in a message."""

    def _parse(self):
        entries, values = self._pre_parse()
        self._value = []
        for sub_values in values:
            if sub_values is Unavailable:
                self._value.append(Unavailable)
            else:
                self._value.extend(sub_values)
        self._entries = entries

    def __iter__(self):
        # pylint: disable=not-an-iterable
        return iter(v for v in self.value if okay(v))


class DirectivesView(HeaderView):           # pylint: disable=abstract-method

    """Wraps a header whose parsed value is a list of directives."""

    knowledge_module = None

    def _process_parsed(self, entry, ds):
        return [self._process_directive(entry, d) for d in ds]

    def _process_directive(self, entry, directive_with_argument):
        directive, argument = directive_with_argument
        parser = self.knowledge_module.parser_for(directive)
        if argument is None:
            if self.knowledge_module.argument_required(directive):
                self.message.complain(1156, entry=entry, directive=directive)
                argument = Unavailable
        else:
            if self.knowledge_module.no_argument(directive):
                self.message.complain(1157, entry=entry, directive=directive)
                argument = None
            elif parser is not None:
                argument = simple_parse(argument, parser,
                                        self.message.complain, 1158,
                                        place=entry,
                                        directive=directive, value=argument)
        return Parametrized(directive, argument)

    def __getattr__(self, key):
        return self[getattr(self.knowledge_module.known, key)]

    def __getitem__(self, key):
        for directive, argument in self:
            if directive == key:
                return True if argument is None else argument
        return None


class CacheControlView(DirectivesView, MultiHeaderView):

    """Wraps a ``Cache-Control`` header."""

    knowledge_module = cache_directive

    def _process_directive(self, entry, directive_with_argument):
        (directive, argument) = directive_with_argument
        if argument is not None:
            (symbol, argument) = argument

            if cache_directive.quoted_string_preferred(directive) and \
                    symbol is not quoted_string:
                self.message.complain(1154, directive=directive)

            if cache_directive.token_preferred(directive) and \
                    symbol is not token:
                self.message.complain(1155, directive=directive)

        return super(CacheControlView, self). \
            _process_directive(entry, (directive, argument))


class StrictTransportSecurityView(DirectivesView, SingleHeaderView):

    """Wraps a ``Strict-Transport-Security`` header."""

    knowledge_module = httpolice.known.hsts_directive


class AltSvcView(SingleHeaderView):

    """Wraps an ``Alt-Svc`` header with its various parameters."""

    def _process_parsed(self, entry, parsed):
        if parsed == u'clear':
            return parsed

        # Parse every parameter's value according to its defined parser.
        parsed = copy.deepcopy(parsed)
        for alternative in parsed:
            params = alternative.param.sequence
            for i in range(len(params)):
                (name, value) = params[i]
                parser = alt_svc_param.parser_for(name)
                if parser is not None:
                    value = simple_parse(value, parser,
                                         self.message.complain, 1259,
                                         place=entry, param=name, value=value)
                params[i] = (name, value)

        return parsed


class PreferView(DirectivesView, MultiHeaderView):

    """Wraps a `Prefer` header."""

    knowledge_module = httpolice.known.preference

    # Each preference has two level of wrapping: ``((name, value), params)``.
    # Params are currently not used for anything, so we peel them off
    # (but they are still part of ``self.value``).

    def _process_parsed(self, entry, ds):
        return [Parametrized(self._process_directive(entry, d), params)
                for (d, params) in ds]

    def __getitem__(self, key):
        for (preference, value) in self.without_params:
            if preference == key:
                return True if value is None else value
        return None

    @property
    def without_params(self):
        return [pref for (pref, _) in self]


class PreferenceAppliedView(DirectivesView, MultiHeaderView):

    """Wraps a ``Preference-Applied`` header."""

    knowledge_module = httpolice.known.preference
