# -*- coding: utf-8; -*-

from httpolice import message


class Request(message.Message):

    def __repr__(self):
        return '<Request %s>' % self.method

    def __init__(self, method_, target, version_, header_entries,
                 body=None, trailer_entries=None, raw=None):
        super(Request, self).__init__(version_, header_entries,
                                      body, trailer_entries, raw)
        self.method = method_
        self.target = target


def check_request(req):
    message.check_message(req)
