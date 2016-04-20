# -*- coding: utf-8; -*-

import argparse
import sys

from httpolice import inputs, reports
from httpolice.exchange import check_exchange
from httpolice.util.seven import stdio_as_text


def main():
    parser = argparse.ArgumentParser(
        description=u'Run HTTPolice on input files.')
    parser.add_argument(u'-i', u'--input', choices=inputs.formats,
                        required=True)
    parser.add_argument(u'-o', u'--output', choices=reports.formats,
                        default=u'text')
    parser.add_argument(u'path', nargs='+')
    args = parser.parse_args()
    input_ = inputs.formats[args.input]
    report = reports.formats[args.output]
    stdout = stdio_as_text(sys.stdout)
    def generate_exchanges():
        for exch in input_(args.path):
            check_exchange(exch)
            yield exch
    try:
        report(generate_exchanges(), stdout)
    except (OSError, RuntimeError) as exc:
        sys.stderr.write('Error: %s\n' % exc)
        sys.exit(1)

if __name__ == '__main__':
    main()
