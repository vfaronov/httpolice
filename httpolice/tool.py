# -*- coding: utf-8; -*-

import argparse
import io
import sys

from httpolice import HTMLReport, TextReport, analyze_streams
from httpolice.util.seven import stdio_as_text


def main():
    parser = argparse.ArgumentParser(
        description=u'Run HTTPolice on two streams (inbound and outbound).')
    parser.add_argument(u'-s', u'--scheme', default=u'http',
                        help=u'URI scheme of the protocol used on the streams, '
                             u'such as "http" (default) or "https"')
    parser.add_argument(u'-H', u'--html', action=u'store_true',
                        help=u'render HTML report instead of plain text')
    parser.add_argument(u'inbound')
    parser.add_argument(u'outbound')
    args = parser.parse_args()
    with io.open(args.inbound, 'rb') as f:
        inbound_stream = f.read()
    with io.open(args.outbound, 'rb') as f:
        outbound_stream = f.read()
    result = analyze_streams(inbound_stream, outbound_stream,
                             args.scheme.decode('ascii'))
    if args.html:
        report_cls = HTMLReport
    else:
        report_cls = TextReport
    report_cls.render([result], stdio_as_text(sys.stdout))


if __name__ == '__main__':
    main()
