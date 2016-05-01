# -*- coding: utf-8; -*-

import collections

from django.conf import settings
from django.utils.encoding import force_text


backlog = collections.deque(maxlen=getattr(settings, 'HTTPOLICE_BACKLOG', 20))


class HTTPoliceMiddleware(object):

    """Captures and checks HTTP exchanges, saving them for later review."""

    def process_response(self, request, response):
        enable = getattr(settings, 'HTTPOLICE_ENABLE', None)
        if (enable == False) or (enable is None and not settings.DEBUG):
            return response

        # Importing `httpolice` can execute a lot of code,
        # so we only do it when it's really time for action.
        import httpolice

        req_method = force_text(request.method)
        req_headers = httpolice.helpers.headers_from_cgi(request.META)

        try:
            # This can raise `django.http.request.RawPostDataException`, saying
            # "You cannot access body after reading from request's data stream"
            req_body = request.body
        except Exception:
            # ...but `RawPostDataException` is not documented in Django API,
            # so catch everything.
            req_body = None

        # A ``Content-Type`` of ``text/plain`` is automatically added
        # to requests that have none (such as GET requests).
        if req_body == b'' and req_method in [u'GET', u'HEAD', u'DELETE']:
            req_headers = [entry for entry in req_headers
                           if entry != (u'Content-Type', b'text/plain')]

        req = httpolice.Request(
            scheme=force_text(request.scheme),
            method=req_method,
            target=force_text(request.path),
            version=None,
            header_entries=req_headers,
            body=req_body,
        )

        if req_method == u'HEAD':
            # Body is automatically stripped from responses to HEAD,
            # but not at this point in the response lifecycle.
            resp_body = b''
        elif response.streaming:
            resp_body = None        # Unknown.
        else:
            resp_body = response.content

        resp = httpolice.Response(
            version=None,
            status=response.status_code,
            reason=force_text(response.reason_phrase),
            header_entries=[
                (force_text(name), value)
                for (name, value) in response.items()],
            body=resp_body,
        )

        exchange = httpolice.Exchange(req, [resp])
        httpolice.check_exchange(exchange)
        backlog.appendleft(exchange)
        return response
