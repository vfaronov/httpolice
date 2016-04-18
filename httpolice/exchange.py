# -*- coding: utf-8; -*-

from httpolice import request, response
from httpolice.blackboard import Blackboard


class Exchange(Blackboard):

    self_name = u'exch'

    def __repr__(self):
        return 'Exchange(%r, %r)' % (self.request, self.responses)

    def __init__(self, req, resps):
        """
        :type req: Request | None
        :type resp: list[Response]
        """
        super(Exchange, self).__init__()
        for resp in resps:
            resp.request = req
        self.request = req
        self.responses = resps

    @property
    def sub_nodes(self):
        if self.request:
            yield self.request
        for resp in self.responses:
            yield resp


def complaint_box(*args, **kwargs):
    box = Exchange(None, [])
    box.complain(*args, **kwargs)
    return box


def check_exchange(exch):
    if exch.request:
        request.check_request(exch.request)
    response.check_responses(exch.responses)
