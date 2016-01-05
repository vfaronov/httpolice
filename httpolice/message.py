# -*- coding: utf-8; -*-

import httpolice.header_view


class Message(object):

    def __init__(self, report, version, header_entries,
                 stream=None, body=None):
        self.report = report
        self.version = version
        self.header_entries = header_entries
        self.stream = stream
        self.body = body
        self.headers = httpolice.header_view.HeadersView(self)
