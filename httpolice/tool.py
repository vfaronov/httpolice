# -*- coding: utf-8; -*-

import argparse
import sys

from httpolice import HTMLReport, TextReport, analyze_streams


def main():
    parser = argparse.ArgumentParser(
        description='Run HTTPolice on two streams (inbound and outbound).')
    parser.add_argument('-s', '--scheme', default='http',
                        help='URI scheme of the protocol used on the streams, '
                             'such as "http" (default) or "https"')
    parser.add_argument('-H', '--html', action='store_true',
                        help='render HTML report instead of plain text')
    parser.add_argument('inbound')
    parser.add_argument('outbound')
    args = parser.parse_args()
    with open(args.inbound) as f:
        inbound_stream = f.read()
    with open(args.outbound) as f:
        outbound_stream = f.read()
    result = analyze_streams(inbound_stream, outbound_stream, args.scheme)
    if args.html:
        report_cls = HTMLReport
    else:
        report_cls = TextReport
    report_cls.render([result], sys.stdout)


if __name__ == '__main__':
    main()
