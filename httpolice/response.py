# -*- coding: utf-8; -*-

from httpolice import message


class Response(message.Message):

    def __repr__(self):
        return '<Response %d>' % self.status

    def __init__(self, version, status, header_entries,
                 body=None, trailer_entries=None, reason=None, raw=None):
        super(Response, self).__init__(version, header_entries,
                                       body, trailer_entries, raw)
        self.status = status
        self.reason = reason
        self.request = None
