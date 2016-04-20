# -*- coding: utf-8; -*-

import argparse
import sys

import httpolice
from httpolice import inputs, reports
from httpolice.exchange import check_exchange


def main():
    parser = argparse.ArgumentParser(
        description=u'Run HTTPolice on input files.')
    parser.add_argument(u'--version', action='version',
                        version=u'HTTPolice %s' % httpolice.__version__)
    parser.add_argument(u'-i', u'--input', choices=inputs.formats,
                        required=True)
    parser.add_argument(u'-o', u'--output', choices=reports.formats,
                        default=u'text')
    parser.add_argument(u'path', nargs='+')
    args = parser.parse_args()

    input_ = inputs.formats[args.input]
    report = reports.formats[args.output]
    def generate_exchanges():
        for exch in input_(args.path):
            check_exchange(exch)
            yield exch

    # We can't use stdout opened as text (as in Python 3)
    # because it may not be UTF-8 (especially on Windows).
    # Our HTML reports are meant for redirection
    # and are always UTF-8, which is declared in ``meta``.
    # As for text reports, they are mostly ASCII,
    # but when they do contain a non-ASCII character
    # (perhaps from pieces of input data),
    # we don't want to trip over Unicode errors.
    # So we encode all text into UTF-8 and write directly as bytes.
    stdout = sys.stdout.buffer if hasattr(sys.stdout, 'buffer') else sys.stdout

    try:
        report(generate_exchanges(), stdout)
    except (OSError, RuntimeError) as exc:
        sys.stderr.write('Error: %s\n' % exc)
        sys.exit(1)

if __name__ == '__main__':
    main()
