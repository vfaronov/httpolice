# -*- coding: utf-8; -*-

from collections import namedtuple
import functools

from httpolice.notice import all_notices


class Complaint(namedtuple('Complaint', ('notice', 'context'))):

    """A notice as reported in a particular place."""

    __slots__ = ()

    @property
    def id(self):
        """The notice's ID (an integer)."""
        return self.notice.id

    @property
    def severity(self):
        """
        The notice's severity,
        as a member of the :class:`~httpolice.Severity` enumeration.
        """
        return self.notice.severity


class Blackboard(object):

    """Shared state that various parts of the code can "write upon".

    Inspired by the concept from symbolic AI.
    The main ways of "writing upon" a blackboard
    are :meth:`complain` and :func:`derived_property`.
    """

    self_name = u'self'

    def __init__(self):
        self._complaints = []
        self._silenced = set()
        self.memoized = {}

    @property
    def children(self):
        return []

    def complain(self, notice_id, **kwargs):
        """Report a notice on this blackboard."""
        notice = all_notices[notice_id]
        context = dict({self.self_name: self}, **kwargs)
        complaint = Complaint(notice, context)
        if complaint not in self._complaints:
            self._complaints.append(complaint)

    def silence(self, notice_ids):
        """Silence unwanted notices on this object.

        :param notice_ids:
          An iterable of notice IDs that will be silenced on this object,
          so they don't appear in :attr:`notices` or in reports.
        """
        self._silenced.update(notice_ids)
        for child in self.children:
            child.silence(notice_ids)

    @property
    def complaints(self):
        """
        A list of :class:`~httpolice.Complaint` instances
        reported on this object.
        """
        return [complaint for complaint in self._complaints
                if complaint.notice.id not in self._silenced]

    # Inside our codebase, there is a clear distinction
    # between a notice and a complaint.
    # But I don't think we should bother the user with this detail.
    # The less we mention the word "complaint", the better.
    notices = complaints


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
