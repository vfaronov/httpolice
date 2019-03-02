# -*- coding: utf-8; -*-

import sys

import httpolice.reports.html


def main():
    httpolice.reports.html.list_notices(sys.stdout.buffer)

if __name__ == '__main__':
    main()
