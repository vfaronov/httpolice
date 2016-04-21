# -*- coding: utf-8; -*-

import sys

import httpolice.reports.html


def main():
    stdout = sys.stdout.buffer if hasattr(sys.stdout, 'buffer') else sys.stdout
    httpolice.reports.html.list_notices(stdout)

if __name__ == '__main__':
    main()
