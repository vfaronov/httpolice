# -*- coding: utf-8; -*-

import django.http
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_http_methods

from django_httpolice.common import get_setting
from django_httpolice.middleware import backlog


@require_http_methods(['GET', 'HEAD'])
@cache_control(no_cache=True)
def report_view(_):
    """Render an HTML report for the latest captured exchanges."""
    if not get_setting('ENABLE'):
        raise django.http.Http404()

    # Importing `httpolice` can execute a lot of code,
    # so we only do it when it's really time for action.
    import httpolice

    response = django.http.HttpResponse()
    httpolice.html_report(backlog, response)
    return response
