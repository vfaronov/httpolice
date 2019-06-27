import base64
import io
import json
from urllib.parse import urlparse

from httpolice.exchange import Exchange
from httpolice.helpers import pop_pseudo_headers
from httpolice.inputs.common import InputError
from httpolice.known import h, m, st
from httpolice.request import Request
from httpolice.response import Response
from httpolice.structure import FieldName, StatusCode, Unavailable
from httpolice.util.text import decode_path


FIDDLER = [u'Fiddler']
CHROME = [u'WebInspector']
FIREFOX = [u'Firefox']
EDGE = [u'F12 Developer Tools']


def har_input(paths):
    for path in paths:
        # According to the spec, HAR files are UTF-8 with an optional BOM.
        path = decode_path(path)
        with io.open(path, 'rt', encoding='utf-8-sig') as f:
            try:
                data = json.load(f)
            except ValueError as exc:
                raise InputError('%s: bad HAR file: %s' % (path, exc)) from exc
            try:
                creator = data['log']['creator']['name']
                for entry in data['log']['entries']:
                    yield _process_entry(entry, creator, path)
            except (TypeError, KeyError) as exc:
                raise InputError('%s: cannot understand HAR file: %r' %
                                 (path, exc)) from exc


def _process_entry(data, creator, path):
    req = _process_request(data['request'], creator, path)
    resp = _process_response(data['response'], req, creator, path)
    return Exchange(req, [resp] if resp is not None else [])


def _process_request(data, creator, path):
    version, header_entries = _process_message(data, creator)
    method = data['method']
    parsed = urlparse(data['url'])
    scheme = parsed.scheme

    if method == m.CONNECT:
        target = parsed.netloc
    elif any(name == h.host for (name, _) in header_entries):
        # With HAR, we can't tell if the request was to a proxy or to a server.
        # So we force most requests into the "origin form" of the target,
        target = parsed.path
        if parsed.query:
            target += u'?' + parsed.query
    else:
        # However, if the request has no ``Host`` header,
        # the user won't be able to see the target host
        # unless we set the full URL ("absolute form") as the target.
        # To prevent this from having an effect on the proxy logic,
        # we explicitly set `Request.is_to_proxy` to `None` later.
        target = data['url']

    if data['bodySize'] == 0:
        # No body, or a body of length 0 (which we do not distinguish).
        body = b''
    elif data['bodySize'] > 0:
        # A message body was present, but we cannot recover it,
        # because message body is the body *with* ``Content-Encoding``,
        # and HAR does not include that.
        body = Unavailable()
    else:
        # Unknown. Maybe there was a body, maybe there wasn't.
        body = None

    text = None
    post = data.get('postData')
    if post and post.get('text'):
        text = post['text']
        if creator in FIDDLER and method == m.CONNECT and u'Fiddler' in text:
            # Fiddler's HAR export adds a body with debug information
            # to CONNECT requests.
            text = None
            body = b''

    req = Request(scheme, method, target, version, header_entries, body,
                  remark=u'from %s' % path)
    if text is not None:
        req.unicode_body = text
    req.is_to_proxy = None                      # See above.
    return req


def _process_response(data, req, creator, path):
    if data['status'] == 0:          # Indicates error in Chrome.
        return None
    version, header_entries = _process_message(data, creator)
    status = StatusCode(data['status'])
    reason = data['statusText']

    if creator in FIDDLER and req.method == m.CONNECT and status.successful:
        # Fiddler's HAR export adds extra debug headers to CONNECT responses
        # after the tunnel is closed.
        header_entries = [(name, value)
                          for (name, value) in header_entries
                          if name not in [u'EndTime', u'ClientToServerBytes',
                                          u'ServerToClientBytes']]

    # The logic for body is mostly like that for requests (see above).
    if data['bodySize'] == 0 or data['content']['size'] == 0 or \
            status == st.not_modified:      # Firefox also includes body on 304
        body = b''
    elif creator in FIREFOX:
        # Firefox seems to exports bogus bodySize:
        # see test/har_data/firefox_gif.har
        body = None
    # Browsers may set ``bodySize = -1`` even when ``content.size >= 0``.
    elif data['bodySize'] > 0 or data['content']['size'] > 0:
        body = Unavailable()
    else:
        body = None

    resp = Response(version, status, reason, header_entries, body=body,
                    remark=u'from %s' % path)

    if data['content'].get('text') and status != st.not_modified:
        if data['content'].get('encoding', u'').lower() == u'base64':
            try:
                decoded_body = base64.b64decode(data['content']['text'])
            except ValueError:
                pass
            else:
                if creator in FIDDLER and req.method == m.CONNECT and \
                        status.successful and b'Fiddler' in decoded_body:
                    # Fiddler's HAR export adds a body with debug information
                    # to CONNECT responses.
                    resp.body = b''
                else:
                    resp.decoded_body = decoded_body

        elif 'encoding' not in data['content']:
            resp.unicode_body = data['content']['text']

    return resp


def _process_message(data, creator):
    header_entries = [(FieldName(d['name']), d['value'])
                      for d in data['headers']]
    pop_pseudo_headers(header_entries)

    # Web browsers' HAR export poorly reflects the actual traffic on the wire.
    # Their httpVersion can't be trusted, and they often mangle lower-level
    # parts of the protocol, e.g. at the time of writing Chrome sometimes omits
    # the Host header from HTTP/1.1 requests. Just consider their HTTP version
    # to be always unknown, and a lot of this pain goes away.
    version = None
    if data['httpVersion'].startswith(u'HTTP/') and \
            creator not in CHROME + FIREFOX + EDGE:
        version = data['httpVersion']

    return version, header_entries
