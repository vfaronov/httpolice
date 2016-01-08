# -*- coding: utf-8; -*-

import argparse
import sys

from httpolice import report, request, response


def main():
    parser = argparse.ArgumentParser(
        description='Run HTTPolice on two streams (inbound and outbound).')
    parser.add_argument('inbound')
    parser.add_argument('outbound')
    args = parser.parse_args()
    with open(args.inbound) as f:
        req_stream = f.read()
    with open(args.outbound) as f:
        resp_stream = f.read()
    reqs = request.parse_stream(req_stream)
    conn = response.Connection(response.parse_stream(resp_stream, reqs))
    report.TextReport(sys.stdout).render_connection(conn)


if __name__ == '__main__':
    main()
