# -*- coding: utf-8; -*-

from httpolice import parse
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
            (from_trailer, i, field)
            for from_trailer, fields in [(False, self._message.header_entries),
                                         (True, self._message.trailer_entries)]
            for i, field in enumerate(fields or [])
            if (name is None) or (name == field.name)
        ]


class HeaderView(object):

    def __init__(self, message, name):
        self.message = message
        self.name = name
        self._positions = self._value = None

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)

    def _pre_parse(self):
        positions = []
        values = []
        items = self.message.headers.enumerate(self.name)
        for from_trailer, i, entry in items:
            if from_trailer and header.is_bad_for_trailer(self.name):
                continue
            positions.append((from_trailer, i))
            parser = \
                (header.parser_for(self.name) or parse.anything) + parse.eof
            state = parse.State(entry.value)
            try:
                parsed = parser.parse(state)
            except parse.ParseError, e:
                entry.complain(1000, error=e)
                parsed = Unparseable
            values.append(parsed)
        return positions, values

    def _parse(self):
        raise NotImplementedError()

    @property
    def positions(self):
        if self._positions is None:
            self._parse()
        return self._positions

    @property
    def value(self):
        if self._positions is None:
            self._parse()
        return self._value

    @property
    def is_present(self):
        if self._positions is None:
            self._parse()
        return len(self._positions) > 0

    def __nonzero__(self):
        return bool(self.value)


class SingleHeaderView(HeaderView):

    def _parse(self):
        positions, values = self._pre_parse()
        if positions:
            self._value = values[-1]
            self._positions = [positions[-1]]
        else:
            self._value = None
            self._positions = []


class MultiHeaderView(HeaderView):

    def __iter__(self):
        return iter(self.value)

    def __len__(self):
        return len(self.value)

    def __getitem__(self, i):
        return self.value[i]

    def _parse(self):
        positions, values = self._pre_parse()
        self._value = [value            # Concatenate all that have been parsed
                       for sub_values in values
                       if sub_values is not Unparseable
                       for value in sub_values]
        self._positions = positions
