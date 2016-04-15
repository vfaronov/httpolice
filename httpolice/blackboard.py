# -*- coding: utf-8; -*-

from collections import namedtuple
import functools


class Complaint(namedtuple('Complaint', ('notice_ident', 'context'))):

    __slots__ = ()


class Blackboard(object):

    self_name = u'self'

    def __init__(self):
        self.complaints = []
        self.memoized = {}

    def complain(self, notice_ident, **kwargs):
        context = dict({self.self_name: self}, **kwargs)
        complaint = Complaint(notice_ident, context)
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


def derived_property(getter):
    @property
    @functools.wraps(getter)
    def prop(self):
        if getter.__name__ not in self.memoized:
            self.memoized[getter.__name__] = getter(self)
        return self.memoized[getter.__name__]

    @prop.setter
    def prop(self, value):
        self.memoized[getter.__name__] = value

    return prop
