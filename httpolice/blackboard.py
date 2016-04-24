# -*- coding: utf-8; -*-

from collections import namedtuple
import functools

from httpolice import notice


class Complaint(namedtuple('Complaint', ('notice_id', 'context'))):

    __slots__ = ()


class Blackboard(object):

    self_name = u'self'

    def __init__(self):
        self.complaints = []
        self.memoized = {}

    def complain(self, notice_id, **kwargs):
        context = dict({self.self_name: self}, **kwargs)
        complaint = Complaint(notice_id, context)
        if complaint not in self.complaints:
            self.complaints.append(complaint)

    @property
    def notices(self):
        return [notice.notices[complaint.notice_id]
                for complaint in self.complaints]


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
