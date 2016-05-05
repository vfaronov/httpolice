# -*- coding: utf-8; -*-

"""
Because only mitmproxy/mitmdump calls our script, not the other way around,
we can imitate mitmproxy's calls and collect the results.
"""

import io
import os
import tempfile

import pytest

import mitmproxy_httpolice


class Bin(object):

    pass


class FakeMitmdump(object):

    # pylint: disable=attribute-defined-outside-init

    def __init__(self):
        self.opts = []

    def start(self):
        self.context = Bin()
        fd, self.report_path = tempfile.mkstemp()
        os.close(fd)
        argv = [''] + self.opts + [self.report_path]
        mitmproxy_httpolice.start(self.context, argv)

    def flow(self,
             req_scheme, req_method, req_path, req_http_version,
             req_fields, req_content,
             resp_http_version, resp_status_code, resp_reason,
             resp_fields, resp_content):
        flow = Bin()
        flow.request = Bin()
        flow.request.scheme = req_scheme
        flow.request.method = req_method
        flow.request.path = req_path
        flow.request.http_version = req_http_version
        flow.request.headers = Bin()
        flow.request.headers.fields = req_fields
        flow.request.content = req_content
        flow.response = Bin()
        flow.response.http_version = resp_http_version
        flow.response.status_code = resp_status_code
        flow.response.reason = resp_reason
        flow.response.headers = Bin()
        flow.response.headers.fields = resp_fields
        flow.response.content = resp_content
        mitmproxy_httpolice.response(self.context, flow)

    def done(self):
        mitmproxy_httpolice.done(self.context)
        with io.open(self.report_path, 'rb') as f:
            self.report = f.read()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, _exc_value, _traceback):
        if exc_type is None:
            self.done()
        if os.path.exists(self.report_path):
            os.unlink(self.report_path)


@pytest.fixture
def fake_mitmdump(request):                 # pylint: disable=unused-argument
    return FakeMitmdump()


def test_simple(fake_mitmdump):         # pylint: disable=redefined-outer-name
    with fake_mitmdump:
        fake_mitmdump.flow(
            'http',
            'GET', '/', 'HTTP/1.1',
            [
                ('host', 'example.com'),
                ('User-Agent', 'demo'),
            ],
            b'',
            'HTTP/1.1', 200, 'OK',
            [
                ('Content-Type', 'text/plain'),
                ('Content-Length', '14'),
                ('Date', 'Tue, 03 May 2016 14:13:34 GMT'),
            ],
            b'Hello world!\r\n'
        )
    assert fake_mitmdump.report == b''


def test_complex(fake_mitmdump):        # pylint: disable=redefined-outer-name
    with fake_mitmdump:
        fake_mitmdump.flow(
            'http',
            'POST', '/foo-bar?baz=qux', 'HTTP/1.1',
            [
                ('host', 'example.com'),
                ('User-Agent', 'demo'),
                ('Transfer-Encoding', 'chunked'),
                ('content-length', '14'),
                ('content-type', 'application/json'),
            ],
            b'{foo: "bar"}',
            'HTTP/1.1', 201, u'Très bien'.encode('iso-8859-1'),
            [
                ('Content-Type', 'text/plain'),
                ('Content-Length', '14'),
                ('Date', 'Tue, 03 May 2016 14:13:34 GMT'),
            ],
            b'Hello world!\r\n'
        )

        fake_mitmdump.flow(
            'http',
            'GET', '/', 'HTTP/1.1',
            [
                ('host', 'example.com'),
                ('User-Agent', 'demo'),
                ('If-None-Match', '"quux"'),
            ],
            b'',
            'HTTP/1.1', 304, 'Not Modified',
            [
                ('Content-Type', 'text/plain'),
                ('Date', 'Tue, 03 May 2016 14:13:34 GMT'),
                ('content-length', '0'),
            ],
            b''
        )

    assert fake_mitmdump.report == (
        b'------------ request 1 : POST /foo-bar?baz=qux\n'
        b'E 1038 Bad JSON body\n' +
        u'------------ response 1 : 201 Très bien\n'.encode('utf-8') +
        b'C 1073 Possibly missing Location header\n'
        b'------------ request 2 : GET /\n'
        b'------------ response 2 : 304 Not Modified\n'
        b'C 1127 Content-Type in a 304 response\n'
    )


def test_http2(fake_mitmdump):          # pylint: disable=redefined-outer-name
    with fake_mitmdump:
        fake_mitmdump.flow(
            'https',
            'GET', '/index.html', 'HTTP/2.0',
            [
                (':method', 'GET'),
                (':scheme', 'https'),
                (':authority', 'example.com'),
                (':path', '/index.html'),
                ('user-agent', 'demo'),
                ('if-match', 'quux'),
            ],
            b'',
            'HTTP/2.0', 404, None,
            [
                (':status', '404'),
                ('content-type', 'text/plain'),
                ('content-length', '14'),
                ('date', 'Tue, 03 May 2016 14:13:34 GMT'),
                ('connection', 'close'),
            ],
            b'Hello world!\r\n'
        )
    assert fake_mitmdump.report == (
        b'------------ request 1 : GET https://example.com/index.html\n'
        b'E 1000 Malformed if-match header\n'
        b'------------ response 1 : 404 Not Found\n'
        b'E 1244 connection header in an HTTP/2 message\n'
    )


def test_html(fake_mitmdump):           # pylint: disable=redefined-outer-name
    fake_mitmdump.opts = ['-o', 'html']
    with fake_mitmdump:
        fake_mitmdump.flow(
            'http',
            'GET', '/', 'HTTP/1.1',
            [
                ('host', 'example.com'),
                ('User-Agent', 'demo'),
            ],
            b'',
            'HTTP/1.1', 200, 'OK',
            [
                ('Content-Type', 'text/plain'),
                ('Content-Length', '14'),
                ('Date', 'Tue, 03 May 2016 14:13:34 GMT'),
            ],
            b'Hello world!\r\n'
        )
    assert b'<h1>HTTPolice report</h1>' in fake_mitmdump.report


def test_silence(fake_mitmdump):         # pylint: disable=redefined-outer-name
    fake_mitmdump.opts = ['-s', '1087', '-s', '1194']
    with fake_mitmdump:
        fake_mitmdump.flow(
            'http',
            'GET', '/', 'HTTP/1.1',
            [
                ('host', 'example.com'),
                ('User-Agent', 'demo'),
            ],
            b'',
            'HTTP/1.1', 401, 'Unauthorized',
            [
                ('Content-Type', 'text/plain'),
                ('Content-Length', '0'),
            ],
            b''
        )
    assert fake_mitmdump.report == (
        b'------------ request 1 : GET /\n'
        b'------------ response 1 : 401 Unauthorized\n'
        b'C 1110 401 response with no Date header\n'
    )
