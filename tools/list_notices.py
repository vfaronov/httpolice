# -*- coding: utf-8; -*-

import sys

import httpolice.reports.html
from httpolice.util.text import stdio_as_bytes


def main():
    httpolice.reports.html.list_notices(stdio_as_bytes(sys.stdout))

if __name__ == '__main__':
    main()
