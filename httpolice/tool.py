# -*- coding: utf-8; -*-

import argparse
import sys

from httpolice import connection, report


def main():
    parser = argparse.ArgumentParser(
        description='Run HTTPolice on two streams (inbound and outbound).')
    parser.add_argument('-H', '--html', action='store_true',
                        help='render HTML report instead of plain text')
    parser.add_argument('inbound')
    parser.add_argument('outbound')
    args = parser.parse_args()
    with open(args.inbound) as f:
        inbound_stream = f.read()
    with open(args.outbound) as f:
        outbound_stream = f.read()
    conn = connection.parse_two_streams(inbound_stream, outbound_stream)
    if args.html:
        report.HTMLReport(sys.stdout).render_connection(conn)
    else:
        report.TextReport(sys.stdout).render_connection(conn)


if __name__ == '__main__':
    main()
