# -*- coding: utf-8; -*-

import django.http
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_http_methods

import django_httpolice.middleware


@require_http_methods(['GET', 'HEAD'])
@cache_control(no_cache=True)
def report_view(_):
    """Render an HTML report for the latest captured exchanges."""

    # Importing `httpolice` can execute a lot of code,
    # so we only do it when it's really time for action.
    import httpolice

    response = django.http.HttpResponse()
    httpolice.html_report(django_httpolice.middleware.backlog, response)
    return response
