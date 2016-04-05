# -*- coding: utf-8; -*-

import operator

from httpolice import known, parse
from httpolice.known import cache_directive, h, header
import httpolice.known.hsts_directive
from httpolice.structure import Parametrized, Unparseable, okay


class HeadersView(object):

    def __init__(self, message):
        self._message = message
        self._cache = {}

    def __getattr__(self, key):
        return self[getattr(h, key)]

    def __getitem__(self, key):
        if key not in self._cache:
            rule = header.rule_for(key)
            if key == h.cache_control:
                cls = CacheControlView
            elif key == h.strict_transport_security:
                cls = StrictTransportSecurityView
            elif rule in [header.SINGLE, header.SINGLE_LIST]:
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

    def possibly(self, predicate):
        return set(name for name in self.names if predicate(name) != False)


class HeaderView(object):

    def __init__(self, message, name):
        self.message = message
        self.name = name
        self._entries = self._value = None

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)

    def _process_parsed(self, entry, value):
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
                stream = parse.Stream(entry.value,
                                      annotate_classes=known.classes)
                try:
                    parsed = stream.parse(parser, to_eof=True)
                except parse.ParseError, e:
                    self.message.complain(1000, entry=entry, error=e)
                    parsed = Unparseable
                else:
                    parsed = self._process_parsed(entry, parsed)
                    self.message.annotations[(from_trailer, i)] = \
                        stream.collect_annotations()
                    stream.dump_complaints(self.message, entry)
            values.append(parsed)
        return entries, values

    def _parse(self):
        raise NotImplementedError()

    @property
    def entries(self):
        if self._entries is None:
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

    def __nonzero__(self):
        return bool(self.value)


class UnknownHeaderView(HeaderView):

    def _parse(self):
        # RFC 7230 section 3.2.2 permits combining field-values with a comma
        # even if we don't really know what the header is.
        entries, values = self._pre_parse()
        self._value = ','.join(values) if values else None
        self._entries = entries


class SingleHeaderView(HeaderView):

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

    def _compare(self, other, op):
        if isinstance(other, SingleHeaderView):
            return self.is_okay and other.is_okay and \
                op(self.value, other.value)
        else:
            return self.is_okay and okay(other) and op(self.value, other)

    __lt__ = lambda self, other: self._compare(other, operator.lt)
    __le__ = lambda self, other: self._compare(other, operator.le)
    __eq__ = lambda self, other: self._compare(other, operator.eq)
    __ne__ = lambda self, other: self._compare(other, operator.ne)
    __ge__ = lambda self, other: self._compare(other, operator.ge)
    __gt__ = lambda self, other: self._compare(other, operator.gt)


class ListHeaderView(HeaderView):

    def __iter__(self):
        return iter(self.value)

    def __len__(self):
        return len(self.value)

    def __getitem__(self, i):
        return self.value[i]

    def __contains__(self, other):
        # Since multi-headers often contain `Parametrized` values,
        # it's useful to be able to check membership by the item itself,
        # ignoring its parameters.
        # This is handled by :meth:`Parametrized.__eq__`,
        # but it's only invoked when the `Parametrized` is on the left side.
        return any(val == other for val in self.value)

    @property
    def okay(self):
        return [v for v in self if okay(v)]


class MultiHeaderView(ListHeaderView):

    def _parse(self):
        entries, values = self._pre_parse()
        self._value = []
        for sub_values in values:
            if sub_values is Unparseable:
                self._value.append(Unparseable)
            else:
                self._value.extend(sub_values)
        self._entries = entries


class DirectivesView(ListHeaderView):

    knowledge_module = None

    def _process_parsed(self, entry, ds):
        return [self._process_directive(entry, d) for d in ds]

    def _process_directive(self, entry, directive_with_argument):
        directive, argument = directive_with_argument

        def complain(ident, **kwargs):
            self.message.complain(ident, entry=entry,
                                  directive=directive, **kwargs)

        parser = self.knowledge_module.parser_for(directive)
        if argument is None:
            if self.knowledge_module.argument_required(directive):
                complain(1156)
                argument = Unparseable
        else:
            if self.knowledge_module.no_argument(directive):
                complain(1157)
                argument = None
            elif parser is not None:
                stream = parse.Stream(str(argument))
                try:
                    argument = stream.parse(parser, to_eof=True)
                except parse.ParseError, e:
                    complain(1158, error=e)
                    argument = Unparseable
                else:
                    stream.dump_complaints(self.message, entry)

        return Parametrized(directive, argument)

    def __getattr__(self, key):
        return self[getattr(self.knowledge_module.known, key)]

    def __getitem__(self, key):
        for directive, argument in self.okay:
            if directive == key:
                return True if argument is None else argument
        return None


class CacheControlView(DirectivesView, MultiHeaderView):

    knowledge_module = cache_directive

    def _process_directive(self, entry, directive_with_argument):
        directive, argument = directive_with_argument

        def complain(ident, **kwargs):
            self.message.complain(ident, entry=entry,
                                  directive=directive, **kwargs)

        # Here we make use of the fact that `rfc7230.token` returns `unicode`
        # whereas `rfc7230.quoted_string` returns `str`
        # (because a ``<quoted-string>`` may contain non-ASCII characters).
        if isinstance(argument, unicode) and \
                cache_directive.quoted_string_preferred(directive):
            complain(1154)
        if isinstance(argument, str) and \
                cache_directive.token_preferred(directive):
            complain(1155)

        return super(CacheControlView, self). \
            _process_directive(entry, (directive, argument))


class StrictTransportSecurityView(DirectivesView, SingleHeaderView):

    knowledge_module = httpolice.known.hsts_directive
