# -*- coding: utf-8; -*-

"""The command-line interface to HTTPolice."""

import argparse
import collections
import multiprocessing
from six.moves import map
import sys
import traceback

import httpolice
from httpolice import inputs, reports
from httpolice.exchange import check_exchange
from httpolice.notice import Severity
from httpolice.util.text import stdio_as_bytes


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description=u'Run HTTPolice on input files.')
    parser.add_argument(u'--version', action='version',
                        version=u'HTTPolice %s' % httpolice.__version__)
    parser.add_argument(u'-i', u'--input', choices=inputs.formats,
                        required=True, metavar=u'FORMAT',
                        help=u'input format (see the user manual)')
    parser.add_argument(u'-o', u'--output', choices=reports.formats,
                        default=u'text', help=u'output format')
    parser.add_argument(u'-j', u'--jobs', type=int, default=1,
                        help=u'check exchanges in this number of '
                             u'parallel processes')
    parser.add_argument(u'-s', u'--silence', metavar=u'ID', type=int,
                        action='append', help=u'silence the given notice ID')
    parser.add_argument(u'--fail-on',
                        choices=[severity.name for severity in Severity],
                        help=u'exit with a non-zero status '
                             u'if any notices with this or higher severity '
                             u'have been reported')
    parser.add_argument(u'--full-traceback', action='store_true',
                        help=u'do not hide the traceback on exceptions')
    parser.add_argument(u'path', nargs='+')
    return parser.parse_args(argv[1:])


def process_exchange(exch):
    check_exchange(exch)
    import pickle
    with open('exch.pickle', 'wb') as f:
        pickle.dump(exch, f, protocol=2)
    return exch


def run_cli(args, stdout, stderr):
    input_ = inputs.formats[args.input]
    report = reports.formats[args.output]
    n_notices = collections.Counter()

    def preprocess_exchange(exch):
        if args.silence:
            exch.silence(args.silence)
        return exch

    def postprocess_exchange(exch):
        n_notices.update(notice.severity
                         for obj in [exch] + exch.children
                         for notice in obj.notices)
        return exch

    try:
        exchanges = map(preprocess_exchange, input_(args.path))
        if args.jobs == 1:
            exchanges = map(process_exchange, exchanges)
        else:
            pool = multiprocessing.Pool(args.jobs)
            exchanges = pool.imap(process_exchange, exchanges)
        exchanges = map(postprocess_exchange, exchanges)

        # We can't use stdout opened as text (as in Python 3)
        # because it may not be UTF-8 (especially on Windows).
        # Our HTML reports are meant for redirection
        # and are always UTF-8, which is declared in ``meta``.
        # As for text reports, they are mostly ASCII,
        # but when they do contain a non-ASCII character
        # (perhaps from pieces of input data),
        # we don't want to trip over Unicode errors.
        # So we encode all text into UTF-8 and write directly as bytes.
        report(exchanges, stdio_as_bytes(stdout))

    except (EnvironmentError, inputs.InputError) as exc:
        if args.full_traceback:
            traceback.print_exc(file=stderr)
        stderr.write('httpolice: %s\n' % exc)
        return 1

    if args.fail_on is not None:
        for severity in Severity:
            if severity >= Severity[args.fail_on] and n_notices[severity] > 0:
                return 1
    return 0


def excepthook(_type, exc, _traceback):
    sys.stderr.write('httpolice: unhandled exception: %r\n' % exc)
    sys.exit(1)


def main():
    args = parse_args(sys.argv)
    if not args.full_traceback:
        sys.excepthook = excepthook
    sys.exit(run_cli(args, sys.stdout, sys.stderr))

if __name__ == '__main__':
    main()
