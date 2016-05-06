# -*- coding: utf-8; -*-

import base64
import json
import io

# pylint: disable=import-error

try:
    from urllib.parse import urlparse
except ImportError:                             # Python 2
    from urlparse import urlparse

# pylint: enable=import-error

from httpolice import framing1
from httpolice.exchange import Exchange
from httpolice.helpers import pop_pseudo_headers
from httpolice.inputs.common import InputError
from httpolice.known import h, media, st
from httpolice.parse import ParseError, Stream
from httpolice.request import Request
from httpolice.response import Response
from httpolice.structure import FieldName, Unavailable, http11, http2


CHROME = [u'WebInspector']
EDGE = [u'F12 Developer Tools']

# Not sure if "Iceweasel" is actually used, but it won't hurt.
FIREFOX = [u'Firefox', u'Iceweasel']


def har_input(paths):
    for path in paths:
        # According to the spec, HAR files are UTF-8 with an optional BOM.
        with io.open(path, 'rt', encoding='utf-8-sig') as f:
            try:
                data = json.load(f)
            except ValueError as exc:
                raise InputError('%s: bad HAR file: %s' % (path, exc))
            try:
                creator = data['log']['creator']['name']
                for entry in data['log']['entries']:
                    yield _process_entry(entry, creator)
            except (TypeError, KeyError) as exc:
                raise InputError('%s: cannot understand HAR file: %r' %
                                 (path, exc))


def _process_entry(data, creator):
    req = _process_request(data['request'], creator)
    resp = _process_response(data['response'], req, creator)
    return Exchange(req, [resp] if resp is not None else [])


def _process_request(data, creator):
    (version, header_entries, pseudo_headers) = _process_message(data, creator)
    if creator in CHROME and version == http11 and u':host' in pseudo_headers:
        # SPDY exported from Chrome.
        version = None

    method = data['method']

    parsed = urlparse(data['url'])
    scheme = parsed.scheme

    # With HAR, we can't tell if the request was to a proxy or to a server.
    # So we force most requests into the "origin form" of the target,
    # unless the request has no ``Host`` header,
    # in which case we use the "absolute form" just for the user's convenience
    # (otherwise they wouldn't be able to see the target host).
    # To prevent this distinction from having an effect on the proxy logic,
    # we explicitly set `Request.is_to_proxy` to `None` later.
    if any(name == h.host for (name, _) in header_entries):
        target = parsed.path
        if parsed.query:
            target += u'?' + parsed.query
    else:
        target = data['url']

    if data['bodySize'] == 0:
        # No body, or a body of length 0 (which we do not distinguish).
        body = b''
    elif data['bodySize'] > 0:
        # A message body was present, but we cannot recover it,
        # because message body is the body *with* ``Content-Encoding``,
        # and HAR does not include that.
        body = Unavailable
    else:
        # Unknown. Maybe there was a body, maybe there wasn't.
        body = None

    text = None
    post = data.get('postData')
    if post and post.get('text'):
        text = post['text']
        if creator in FIREFOX and \
                post['mimeType'] == media.application_x_www_form_urlencoded \
                and u'\r\n' in text:
            # Yes, Firefox actually outputs this stuff. Go figure.
            (wtf, actual_text) = text.rsplit(u'\r\n', 1)
            try:
                stream = Stream((wtf + u'\r\n').encode('iso-8859-1'))
                more_entries = framing1.parse_header_fields(stream)
            except (UnicodeError, ParseError):
                pass
            else:
                header_entries.extend(more_entries)
                text = actual_text

    req = Request(scheme, method, target, version, header_entries, body)
    if text is not None:
        req.unicode_body = text
    req.is_to_proxy = None                      # See above.
    return req


def _process_response(data, req, creator):
    if data['status'] == 0:          # Indicates error in Chrome.
        return None
    (version, header_entries, _) = _process_message(data, creator)
    status = data['status']
    reason = data['statusText']

    # The logic for body is similar to that for requests (see above),
    # except that
    # (1) Firefox also includes a body with 304 responses;
    # (2) browsers may set ``bodySize = -1`` even when ``content.size >= 0``.
    if data['bodySize'] == 0 or data['content']['size'] == 0 or \
            status == st.not_modified:
        body = b''
    elif data['bodySize'] > 0 or data['content']['size'] > 0:
        body = Unavailable
    else:
        body = None

    if version == http11 and creator in FIREFOX and \
            any(name == u'x-firefox-spdy' for (name, _) in header_entries):
        # Helps with SPDY in Firefox.
        version = None
    if version != req.version:
        # Helps with SPDY in Chrome.
        version = None

    resp = Response(version, status, reason, header_entries, body=body)
    if data['content'].get('text') and status != st.not_modified:
        if data['content'].get('encoding', u'').lower() == u'base64':
            resp.decoded_body = base64.b64decode(data['content']['text'])
        elif 'encoding' not in data['content']:
            resp.unicode_body = data['content']['text']
    return resp


def _process_message(data, creator):
    header_entries = [(FieldName(d['name']), d['value'])
                      for d in data['headers']]
    pseudo_headers = pop_pseudo_headers(header_entries)
    if creator in EDGE:         # Edge exports HTTP/2 messages as HTTP/1.1.
        version = None
    elif data['httpVersion'] == u'HTTP/2.0':          # Used by Firefox.
        version = http2
    elif data['httpVersion'] == u'unknown':           # Used by Chrome.
        version = None
    else:
        version = data['httpVersion']
    return (version, header_entries, pseudo_headers)
