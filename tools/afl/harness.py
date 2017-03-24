# -*- coding: utf-8; -*-

import os
import sys

import httpolice.cli

if __name__ == '__main__':
    args = httpolice.cli.parse_args(sys.argv)
    import afl
    while afl.loop(100):
        httpolice.cli.run_cli(args, sys.stdout, sys.stderr)
    # As suggested by python-afl docs.
    os._exit(0)         # pylint: disable=protected-access
