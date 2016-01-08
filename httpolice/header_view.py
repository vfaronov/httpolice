# -*- coding: utf-8; -*-

from httpolice import known, parse
from httpolice.common import Unparseable
from httpolice.known import h, header


class HeadersView(object):

    def __init__(self, message):
        self._message = message
        self._cache = {}

    def __getattr__(self, key):
        return self[getattr(h, key)]

    def __getitem__(self, key):
        if key not in self._cache:
            if header.is_multi_header(key):
                cls = MultiHeaderView
            else:
                cls = SingleHeaderView
            self._cache[key] = cls(self._message, key)
        return self._cache[key]

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
                continue
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
                state.dump_complaints(entry)
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

    def __nonzero__(self):
        return bool(self.value)


class SingleHeaderView(HeaderView):

    def _parse(self):
        entries, values = self._pre_parse()
        if entries:
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

    def _parse(self):
        entries, values = self._pre_parse()
        self._value = [value            # Concatenate all that have been parsed
                       for sub_values in values
                       if sub_values is not Unparseable
                       for value in sub_values]
        self._entries = entries
