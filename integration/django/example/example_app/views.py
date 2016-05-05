# -*- coding: utf-8; -*-

import json

from django.http import HttpResponse


def my_view(request):
    name = request.GET.get('name')
    format_ = request.GET.get('format', 'json')
    if format_ == 'json':
        content = json.dumps({'hello': name})
        content_type = 'application/json'
    elif format_ == 'plain':
        content = 'Hello %s!\n' % name
        content_type = 'application/json'       # oops!
    return HttpResponse(content, content_type=content_type)
