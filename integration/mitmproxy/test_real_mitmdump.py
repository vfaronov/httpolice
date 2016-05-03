# -*- coding: utf-8; -*-

"""Spin up an actual mitmdump process and run a few requests through it."""

import io
import os
import random
import socket
import ssl
import subprocess
import tempfile
import time

import pytest


class RealMitmdump(object):

    # pylint: disable=attribute-defined-outside-init

    def __init__(self):
        self.port = random.randint(1024, 65535)

    def start(self):
        fd, self.report_path = tempfile.mkstemp()
        os.close(fd)
        script_path = subprocess.check_output(['python', '-m',
                                               'mitmproxy_httpolice']).strip()
        self.process = subprocess.Popen(
            [
                'mitmdump', '-p', str(self.port), '-s',
                "'%s' '%s'" % (script_path, self.report_path)
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        time.sleep(2)       # Give it some time to get up and running

    # This whole thing is actually easier to do by hand
    # than with either `httplib` or `urllib2`,
    # and I don't want to pull in Requests just for this.

    def send_request(self, data):
        # pylint: disable=no-member
        sock = socket.create_connection(('localhost', self.port))
        sock.sendall(data)
        sock.recv(4096)
        sock.close()

    def send_tunneled_request(self, host, port, data):
        # We need our own TLS context that does not verify certificates.
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        sock = socket.create_connection(('localhost', self.port))
        connect = (u'CONNECT {0}:{1} HTTP/1.1\r\n'
                   u'Host: {0}\r\n'
                   u'\r\n'.format(host, port))
        sock.sendall(connect.encode('iso-8859-1'))
        assert sock.recv(4096).startswith(b'HTTP/1.1 2')
        sock = context.wrap_socket(sock, server_hostname=host)
        sock.sendall(data)
        sock.recv(4096)
        sock.close()

    def done(self, collect=True):
        self.process.terminate()
        self.process.communicate()
        if collect:
            with io.open(self.report_path, 'rb') as f:
                self.report = f.read()
        if os.path.exists(self.report_path):
            os.remove(self.report_path)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, _exc_value, _traceback):
        self.done(collect=exc_type is None)


@pytest.fixture
def real_mitmdump(request):                  # pylint: disable=unused-argument
    return RealMitmdump()


def test_real(real_mitmdump):           # pylint: disable=redefined-outer-name
    with real_mitmdump:
        real_mitmdump.send_request(
            b'GET http://httpbin.org/response-headers?ETag=foobar HTTP/1.1\r\n'
            b'Host: httpbin.org\r\n'
            b'\r\n'
        )
        real_mitmdump.send_tunneled_request(
            'httpd.apache.org', 443,
            b'OPTIONS * HTTP/1.1\r\n'
            b'Host: ietf.org\r\n'
            b'User-Agent: demo\r\n'
            b'Content-Length: 14\r\n'
            b'\r\n'
            b'Hello world!\r\n'
        )
    assert real_mitmdump.report == (
        b'------------ request 1 : GET /response-headers?ETag=foobar\n'
        b'C 1070 No User-Agent header\n'
        b'------------ response 1 : 200 OK\n'
        b'E 1000 Malformed ETag header\n'
        b'------------ request 2 : OPTIONS *\n'
        b'C 1041 Body without Content-Type\n'
        b'E 1062 OPTIONS request with a body but no Content-Type\n'
    )
