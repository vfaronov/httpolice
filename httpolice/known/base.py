# -*- coding: utf-8; -*-

class KnownDict(object):

    def __init__(self, cls, items, extra_info=None, name_from_title=False):
        self.cls = cls
        allowed_info = set(['_', '_citations', '_no_sync', '_title'] +
                           (extra_info or []))
        self._name_from_title = name_from_title
        self._by_key = {}
        self._by_name = {}
        for item in items:
            assert set(item).issubset(allowed_info)
            key = item['_']
            assert key not in self._by_key
            self._by_key[key] = item
            name = self._name_for(item)
            assert name not in self._by_name
            self._by_name[name] = key

    def __getattr__(self, name):
        if name in self._by_name:
            return self._by_name[name]
        else:
            raise AttributeError(name)

    def __getitem__(self, key):         # pragma: no cover
        return self._by_key[key]

    def __iter__(self):
        return iter(self._by_key)

    def __contains__(self, key):
        return key in self._by_key

    def get_info(self, key):
        return self._by_key.get(key, {})

    def _name_for(self, item):
        name = item['_title'] if self._name_from_title else item['_']
        name = (name.
                replace(u'-', u' ').replace(u' ', u'_').replace(u'/', u'_').
                replace(u'+', u'_').replace(u'.', u'_').
                lower())
        if name in [u'continue', u'from', u'return']:
            name = name + u'_'
        return name
