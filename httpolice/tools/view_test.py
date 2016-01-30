# -*- coding: utf-8; -*-

import argparse
from os import listdir
from os.path import abspath, dirname, join
import sys

from httpolice import HTMLReport, analyze_streams
import httpolice.test


def main():
    parser = argparse.ArgumentParser(
        description='Run HTTPolice on its own test file(s) '
                    'and view the result as an HTML report.')
    parser.add_argument('prefix', nargs='*')
    args = parser.parse_args()
    root = abspath(join(dirname(__file__), '..', 'test_data'))
    result = []
    for filename in listdir(root):
        if any(filename.startswith(prefix) for prefix in args.prefix):
            inbound, outbound, scheme, _ = \
                httpolice.test.load_test_file(join(root, filename))
            result.append(analyze_streams(inbound, outbound, scheme))
    HTMLReport.render(result, sys.stdout)


if __name__ == '__main__':
    main()
