# -*- coding: utf-8; -*-

import argparse
from os import listdir
from os.path import abspath, dirname, join
import sys

from httpolice import HTMLReport, TextReport, analyze_streams
import httpolice.test
from httpolice.util.seven import stdio_as_text


def main():
    parser = argparse.ArgumentParser(
        description=u'Run HTTPolice on its own test file(s) '
                    u'and view the result as a report.')
    parser.add_argument(u'-H', u'--html', action=u'store_true',
                        help=u'render HTML report instead of plain text')
    parser.add_argument(u'prefix', nargs=u'*')
    args = parser.parse_args()
    root = abspath(join(dirname(__file__), '..', 'test_data'))
    result = []
    for filename in listdir(root):
        if any(filename.startswith(prefix) for prefix in args.prefix):
            inbound, outbound, scheme, _ = \
                httpolice.test.load_test_file(join(root, filename))
            result.extend(analyze_streams(inbound, outbound, scheme))
    report_cls = HTMLReport if args.html else TextReport
    report_cls.render(result, stdio_as_text(sys.stdout))


if __name__ == '__main__':
    main()
