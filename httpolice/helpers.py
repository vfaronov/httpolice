# -*- coding: utf-8; -*-

"""Functions that may be useful for integrating with HTTPolice."""

import six

from httpolice.util.text import force_bytes, force_unicode


__all__ = ['headers_from_cgi']


def headers_from_cgi(cgi_dict):
    """Convert CGI variables into header entries.

    :param cgi_dict:
        A mapping of CGI-like meta-variables,
        as found in (for example) WSGI's `environ`
        or :attr:`django.http.HttpRequest.META`.
    :return:
        A list of header entries,
        suitable for passing into :class:`httpolice.Request`.
    """
    names = []
    # ``Host`` should come first according to RFC 7230 Section 5.4.
    for default_name in ['HTTP_HOST', 'CONTENT_LENGTH', 'CONTENT_TYPE']:
        if cgi_dict.get(default_name):
            names.append(default_name)
    for name in cgi_dict:
        if name.startswith('HTTP_') and name not in names:
            names.append(name)
    return [
        (_header_name_from_cgi(name), _header_value_from_cgi(cgi_dict[name]))
        for name in names]


def _header_name_from_cgi(cgi_name):
    prefix = 'HTTP_'
    if cgi_name.startswith(prefix):
        cgi_name = cgi_name[len(prefix):]
    return force_unicode('-'.join(p.title() for p in cgi_name.split('_')))


def _header_value_from_cgi(value):
    if not isinstance(value, (six.text_type, bytes)):
        value = str(value)
    return force_bytes(value)
