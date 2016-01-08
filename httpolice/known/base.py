# -*- coding: utf-8; -*-

class KnownDict(object):

    def __init__(self, items, extra_info=None):
        allowed_info = set(['_', '_citations'] + (extra_info or []))
        self._by_key = {}
        self._by_name = {}
        for item in items:
            assert set(item).issubset(allowed_info)
            key = item['_']
            assert key not in self._by_key
            self._by_key[key] = item
            name = self._name_for(item)
            assert name not in self._by_name
            self._by_name[name] = item

    def __getattr__(self, name):
        if name in self._by_name:
            return self._by_name[name]['_']
        else:
            raise AttributeError(name)

    def __getitem__(self, key):
        return self._by_key[key]

    def get_info(self, key):
        return self._by_key.get(key, {})

    def __iter__(self):
        return iter(self._by_key)

    def __contains__(self, key):
        return key in self._by_key

    @classmethod
    def _name_for(cls, item):
        return item['_'].replace(u'-', u' ').replace(u' ', u'_').lower()
