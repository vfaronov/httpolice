#!/bin/sh

set -e

test -e setup.py || { echo 'must run from repo root' >&2; exit 1; }

if [ "$TRAVIS_PYTHON_VERSION" = 3.6 ]; then
    # Pylint on HTTPolice doesn't work under Python 3.6
    # with the current versions of astroid (1.4.9 and master).
    echo 'WARNING: skipping Pylint under Python 3.6' >&2
    exit 0
fi

find . -name '*.py' | grep -Fv ./doc/conf.py | xargs pylint "$@"
