# -*- coding: utf-8; -*-

import functools


class Blackboard(object):

    self_name = 'self'

    def __init__(self):
        self.complaints = None
        self.memoized = {}

    def complain(self, notice_ident, **kwargs):
        if self.complaints is None:
            self.complaints = []
        context = dict({self.self_name: self}, **kwargs)
        complaint = (notice_ident, context)
        if complaint not in self.complaints:
            self.complaints.append(complaint)

    @property
    def sub_nodes(self):
        return []

    def collect_complaints(self):
        for node in self.sub_nodes:
            for c in node.collect_complaints():
                yield c
        for c in self.complaints or []:
            yield c


def memoized_property(getter):
    @property
    @functools.wraps(getter)
    def inner_getter(self):
        if getter.__name__ not in self.memoized:
            self.memoized[getter.__name__] = getter(self)
        return self.memoized[getter.__name__]
    return inner_getter
