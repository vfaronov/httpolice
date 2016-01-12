# -*- coding: utf-8; -*-

from httpolice import known, parse
from httpolice.common import Unparseable, okay
from httpolice.known import h, header


class HeadersView(object):

    def __init__(self, message):
        self._message = message
        self._cache = {}

    def __getattr__(self, key):
        return self[getattr(h, key)]

    def __getitem__(self, key):
        if key not in self._cache:
            rule = header.rule_for(key)
            if rule == header.SINGLE:
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
                        self._message.trailer_entries or []]:
            for entry in entries:
                if entry.name not in seen:
                    yield entry.name
                    seen.add(entry.name)

    def __iter__(self):
        for name in self.names:
            yield self[name]

    def enumerate(self, name=None):
        return [
            (from_trailer, field)
            for from_trailer, fields in [(False, self._message.header_entries),
                                         (True, self._message.trailer_entries)]
            for field in fields or []
            if (name is None) or (name == field.name)
        ]


class HeaderView(object):

    def __init__(self, message, name):
        self.message = message
        self.name = name
        self._entries = self._value = None

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)

    def _pre_parse(self):
        entries = []
        values = []
        items = self.message.headers.enumerate(self.name)
        for from_trailer, entry in items:
            if from_trailer and header.is_bad_for_trailer(self.name):
                entry.complain(1026)
            entries.append(entry)
            parser = \
                (header.parser_for(self.name) or parse.anything) + parse.eof
            state = parse.State(entry.value, annotate_classes=known.classes)
            try:
                parsed = parser.parse(state)
            except parse.ParseError, e:
                entry.complain(1000, error=e)
                parsed = Unparseable
            else:
                entry.annotated = state.collect_annotations()
                state.dump_complaints(entry, entry)
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
                self.message.complain(1013, header=self, entries=entries)
            self._value = values[-1]
            self._entries = [entries[-1]]
        else:
            self._value = None
            self._entries = []


class MultiHeaderView(HeaderView):

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

    def _parse(self):
        entries, values = self._pre_parse()
        self._value = [value            # Concatenate all that have been parsed
                       for sub_values in values
                       if sub_values is not Unparseable
                       for value in sub_values]
        self._entries = entries
