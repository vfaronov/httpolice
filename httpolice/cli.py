# -*- coding: utf-8; -*-

"""The command-line interface to HTTPolice."""

import argparse
import sys

import httpolice
from httpolice import inputs, reports
from httpolice.exchange import check_exchange
from httpolice.util.text import stdio_as_bytes


def run_cli(argv, stdout, stderr):
    parser = argparse.ArgumentParser(
        description=u'Run HTTPolice on input files.')
    parser.add_argument(u'--version', action='version',
                        version=u'HTTPolice %s' % httpolice.__version__)
    parser.add_argument(u'-i', u'--input', choices=inputs.formats,
                        required=True, metavar=u'FORMAT',
                        help=u'input format (see the user manual)')
    parser.add_argument(u'-o', u'--output', choices=reports.formats,
                        default=u'text', help=u'output format')
    parser.add_argument(u'-s', u'--silence', metavar=u'ID', type=int,
                        action='append', help=u'silence the given notice ID')
    parser.add_argument(u'path', nargs='+')
    args = parser.parse_args(argv[1:])

    input_ = inputs.formats[args.input]
    report = reports.formats[args.output]
    def generate_exchanges():
        for exch in input_(args.path):
            if args.silence:
                exch.silence(args.silence)
            check_exchange(exch)
            yield exch

    try:
        # We can't use stdout opened as text (as in Python 3)
        # because it may not be UTF-8 (especially on Windows).
        # Our HTML reports are meant for redirection
        # and are always UTF-8, which is declared in ``meta``.
        # As for text reports, they are mostly ASCII,
        # but when they do contain a non-ASCII character
        # (perhaps from pieces of input data),
        # we don't want to trip over Unicode errors.
        # So we encode all text into UTF-8 and write directly as bytes.
        report(generate_exchanges(), stdio_as_bytes(stdout))
    except (EnvironmentError, inputs.InputError) as exc:
        stderr.write('httpolice: %s\n' % exc)
        return 1

    return 0


def excepthook(_type, exc, _traceback):
    sys.stderr.write('httpolice: unhandled exception: %r\n' % exc)
    sys.exit(1)


def main():
    sys.excepthook = excepthook
    sys.exit(run_cli(sys.argv, sys.stdout, sys.stderr))

if __name__ == '__main__':
    main()
