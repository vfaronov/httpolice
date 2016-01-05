# -*- coding: utf-8; -*-

from httpolice import common, parse, syntax
from httpolice.header import known_headers as h


class HeadersView(object):

    def __init__(self, message):
        self._message = message
        self._cache = {}

    def __getattr__(self, key):
        return self[getattr(h, key)]

    def __getitem__(self, key):
        if key not in self._cache:
            cls = _cls_for(key) or MultiHeaderView
            self._cache[key] = cls(self._message, key)
        return self._cache[key]

    def get_entries(self, name=None):
        return [field for field in self._message.header_entries
                if (name is None) or (name == field.name)]


class HeaderView(object):

    def __init__(self, message, name):
        self.message = message
        self.name = name
        self._entries = self._value = None

    def __repr__(self):
        return u'<%s %s>' % (self.__class__.__name__, self.name)

    def _walk(self):
        self._entries = [entry
                         for entry in self.message.header_entries
                         if entry.name == self.name]
        parser = _parser_for(self.name) or parse.anything
        self._value = self._parse(self.entries, parser)

    def _parse(self, entries, parser):
        raise NotImplementedError()

    @property
    def entries(self):
        if self._entries is None:
            self._walk()
        return self._entries

    @property
    def value(self):
        if self._entries is None:
            self._walk()
        return self._value

    @property
    def is_present(self):
        if self._entries is None:
            self._walk()
        return len(self._entries) > 0

    @property
    def is_absent(self):
        return not self.is_present

    def __nonzero__(self):
        return bool(self.value)


class SingleHeaderView(HeaderView):

    def _parse(self, entries, parser):
        r = None
        for entry in entries:
            state = parse.State(entry.value)
            try:
                r = parser.parse(state)
            except parse.ParseError:
                r = common.Unparseable
        return r


class MultiHeaderView(HeaderView):

    container = syntax.comma_list

    def _parse(self, entries, inner_parser):
        rs = []
        for entry in entries:
            state = parse.State(entry.value)
            try:
                rs.extend(self.container(inner_parser).parse(state))
            except parse.ParseError:
                rs.append(common.Unparseable)
        return rs


class Multi1HeaderView(MultiHeaderView):

    container = syntax.comma_list1


_parse_rules = {
    h.content_length: (SingleHeaderView, syntax.integer),
}

def _cls_for(name):
    return _parse_rules.get(name, (None, None))[0]

def _parser_for(name):
    return _parse_rules.get(name, (None, None))[1]
