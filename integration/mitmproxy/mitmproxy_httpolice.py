# -*- coding: utf-8; -*-

import argparse
import io
import os

import httpolice


__version__ = '0.2.0'

reports = {'text': httpolice.text_report, 'html': httpolice.html_report}


def start(context, argv):
    parser = argparse.ArgumentParser(prog=os.path.basename(__file__),
                                     add_help=False)
    parser.add_argument('-o', '--output', choices=reports, default='text')
    parser.add_argument('-s', '--silence', metavar='ID',
                        type=int, action='append')
    parser.add_argument('report_path')
    context.args = parser.parse_args(argv[1:])

    # Open the output file right now, because if it's wrong,
    # we don't want to wait until the end and lose all collected data.
    path = os.path.expanduser(context.args.report_path)
    context.report_file = io.open(path, 'wb')

    context.exchanges = []


def response(context, flow):
    req = construct_request(flow)
    resp = construct_response(flow)
    exch = httpolice.Exchange(req, [resp])
    if context.args.silence:
        exch.silence(context.args.silence)
    httpolice.check_exchange(exch)
    context.exchanges.append(exch)


def done(context):
    with context.report_file:
        report = reports[context.args.output]
        report(context.exchanges, context.report_file)


def construct_request(flow):
    version, headers, body = extract_message_basics(flow.request)
    scheme = decode(flow.request.scheme)
    method = decode(flow.request.method)

    # Contrary to mitmproxy's docs, `flow.request.path` will actually be "*"
    # for asterisk-form requests in the tunnel (after CONNECT).
    # Authority-form and absolute-form requests in the tunnel
    # are simply rejected as errors by mitmproxy, closing the connection.
    # As for `flow.request.first_line_format`,
    # I couldn't get that to be anything other than "relative".
    target = decode(flow.request.path)

    if version == u'HTTP/2':
        pseudo_headers = httpolice.helpers.pop_pseudo_headers(headers)
        authority = pseudo_headers.get(u':authority')
        has_host = any(k.lower() == u'host' for (k, v) in headers)
        if authority and not has_host and target.startswith(u'/'):
            # Reconstruct HTTP/2's equivalent of
            # the "absolute form" of request target (RFC 7540 Section 8.1.2.3).
            target = scheme + u'://' + authority + target

    return httpolice.Request(scheme, method, target, version, headers, body)


def construct_response(flow):
    version, headers, body = extract_message_basics(flow.response)
    status = flow.response.status_code
    reason = decode(flow.response.reason)
    if version == u'HTTP/2':
        httpolice.helpers.pop_pseudo_headers(headers)
    if (100 <= status < 200) or status in [204, 304]:
        headers = remove_content_length(headers, only_if=b'0')
    return httpolice.Response(version, status, reason, headers, body)


def extract_message_basics(msg):
    version = decode(msg.http_version)
    if version == u'HTTP/2.0':
        version = u'HTTP/2'
    headers = [(decode(k), v) for (k, v) in msg.headers.fields]
    if any(k.lower() == u'transfer-encoding' for (k, v) in headers):
        headers = remove_content_length(headers)
    body = msg.content
    return version, headers, body


def remove_content_length(headers, only_if=None):
    # mitmproxy automatically adds a ``Content-Length`` header
    # to messages that lack it.
    # But some messages can't/shouldn't have a ``Content-Length`` at all.
    return [(k, v)
            for (k, v) in headers
            if k.lower() != u'content-length' or (only_if and v != only_if)]


def decode(s):
    if isinstance(s, bytes):
        return s.decode('iso-8859-1')
    else:
        return s


if __name__ == '__main__':                      # pragma: no cover
    # Print the path to this script,
    # for substitution into the mitmproxy command.
    print(__file__)
