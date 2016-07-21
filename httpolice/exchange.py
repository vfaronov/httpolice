# -*- coding: utf-8; -*-

from httpolice import request, response
from httpolice.blackboard import Blackboard


class Exchange(Blackboard):

    # Note that an exchange is a :class:`Blackboard`,
    # so notices can be reported directly on it.
    # See :func:`complaint_box`.

    self_name = u'exch'

    def __repr__(self):
        return 'Exchange(%r, %r)' % (self.request, self.responses)

    def __init__(self, req, resps):
        """
        :param req:
            The request, as a :class:`~httpolice.Request` object.
            If it is not available, you can pass `None`,
            and the responses will be checked on their own.
            However, this **disables many checks**
            which rely on context information from the request.
        :param resps:
            The responses to `req`,
            as a list of :class:`~httpolice.Response` objects.
            Usually this will be a list of 1 element.
            If you only want to check the request, pass an empty list ``[]``.
        """
        super(Exchange, self).__init__()
        for resp in resps:
            resp.request = req
        self.request = req
        self.responses = resps

    @property
    def children(self):
        r = super(Exchange, self).children
        if self.request is not None:
            r.append(self.request)
        r.extend(self.responses)
        return r


def complaint_box(*args, **kwargs):
    """Create an empty exchange that only carries a single notice.

    This is used (for example, in :mod:`httpolice.framing1`)
    to report notices that do not correspond to any particular message.
    """
    box = Exchange(None, [])
    box.complain(*args, **kwargs)
    return box


def check_exchange(exch):
    """Run all checks on the exchange `exch`, modifying it in place."""
    if exch.request:
        request.check_request(exch.request)
    response.check_responses(exch.responses)
