# -*- coding: utf-8; -*-


class Blackboard(object):

    __slots__ = ('complaints',)

    self_name = 'self'

    def __init__(self):
        self.complaints = None

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
