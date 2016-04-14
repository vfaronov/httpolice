# -*- coding: utf-8; -*-

from httpolice import request, response
from httpolice.blackboard import Blackboard


class ExchangeView(Blackboard):

    self_name = u'exch'

    def __repr__(self):
        return 'ExchangeView(%r, %r)' % (self.request, self.responses)

    def __init__(self, req, resps):
        """
        :type req: RequestView
        :type resp: list[ResponseView]
        """
        super(ExchangeView, self).__init__()
        assert all(resp.request is req for resp in resps)
        self.request = req
        self.responses = resps

    @property
    def sub_nodes(self):
        if self.request:
            yield self.request
        for resp in self.responses:
            yield resp


def complaint_box(*args, **kwargs):
    box = ExchangeView(None, [])
    box.complain(*args, **kwargs)
    return box


def analyze_exchange(exch):
    """
    :type exch: structure.Exchange
    """
    req_view = request.RequestView(exch.request) if exch.request else None
    resp_views = [response.ResponseView(req_view, resp)
                  for resp in exch.responses or []]
    exch = ExchangeView(req_view, resp_views)
    check_exchange(exch)
    return exch


def check_exchange(exch):
    if exch.request:
        request.check_request(exch.request)
    response.check_responses(exch.responses)
