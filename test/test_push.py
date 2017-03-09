import six

from httpolice import (
    Exchange,
    Request,
    Response,
    check_exchange,
    html_report,
    text_report,
)


def _pushed_exchange(**kwargs):
    req_kwargs = dict(scheme=u'https',
                      method=u'GET', target=u'https://example.com/',
                      version=u'HTTP/2',
                      header_entries=[],
                      body=b'')
    req_kwargs.update(**kwargs)
    req = Request(promised=True, **req_kwargs)
    resp = Response(req.version, 200, u'OK',
                    [
                        (u'Date', b'Tue, 07 Mar 2017 17:22:28 GMT'),
                        (u'Content-Type', b'text/plain'),
                        (u'Content-Length', b'14'),
                        (u'Cache-Control', b'max-age=86400'),
                    ],
                    b'Hello world!\r\n')
    return Exchange(req, [resp])


def _check(exch, expected):
    check_exchange(exch)
    buf = six.BytesIO()
    text_report([exch], buf)
    actual = [int(ln[2:6])
              for ln in buf.getvalue().decode('utf-8').splitlines()
              if not ln.startswith(u'----')]
    assert sorted(expected) == sorted(actual)
    html_report([exch], six.BytesIO())      # Just check that it doesn't fail


def test_promised_request():
    exch = _pushed_exchange(
        header_entries=[(u'ETag', b'"just something to trigger a notice"')])
    check_exchange(exch)

    buf = six.BytesIO()
    text_report([exch], buf)
    assert buf.getvalue().startswith(b'------------ promised request: ')

    buf = six.BytesIO()
    html_report([exch], buf)
    assert b'Promised request' in buf.getvalue()


def test_1296_1():
    _check(_pushed_exchange(method=u'DELETE'),
           [1296, 1297])


def test_1297():
    # POST is theoretically cacheable, but unsafe.
    _check(_pushed_exchange(method=u'POST',
                            header_entries=[(u'Content-Length', b'0')]),
           [1297])


def test_1298():
    _check(_pushed_exchange(method=u'GET',
                            header_entries=[(u'Content-Type', b'text/plain')],
                            body=b'Hello world!\r\n'),
           [1298, 1056])


def test_1299():
    _check(_pushed_exchange(target=u'/', version=u'HTTP/1.1',
                            header_entries=[(u'Host', b'example.com')]),
           [1299])
