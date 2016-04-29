# -*- coding: utf-8; -*-

from collections import namedtuple
import functools

from httpolice import notice


class Complaint(namedtuple('Complaint', ('notice_id', 'context'))):

    """An instance of a notice in a particular place (context)."""

    __slots__ = ()


class Blackboard(object):

    """Shared state that various parts of the code can "write upon".

    Inspired by the concept from symbolic AI.
    The main ways of "writing upon" a blackboard
    are :meth:`complain` and :func:`derived_property`.
    """

    self_name = u'self'

    def __init__(self):
        self.complaints = []
        self.memoized = {}

    def complain(self, notice_id, **kwargs):
        """Report a notice on this blackboard."""
        context = dict({self.self_name: self}, **kwargs)
        complaint = Complaint(notice_id, context)
        if complaint not in self.complaints:
            self.complaints.append(complaint)

    @property
    def notices(self):
        return [notice.notices[complaint.notice_id]
                for complaint in self.complaints]


def derived_property(getter):
    """A property that can be derived from a blackboard's underlying data.

    For example, a `Request` blackboard is initialized with
    a `body` property (the payload body), which doesn't change afterwards.
    But some parts of the code want the `decoded_body` instead.
    If we have the `body`, we can derive the `decoded_body` and memoize it.

    On the other hand, in HAR files, we never know the raw `body`
    (so it is always set to `Unavailable`),
    but sometimes we do know the `decoded_body`,
    so the HAR input module may assign directly to `decoded_body`.
    """

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
