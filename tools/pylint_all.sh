#!/bin/sh

set -e

test -e setup.py || { echo 'must run from repo root' >&2; exit 1; }

find . -name '*.py' | grep -Fv ./doc/conf.py | xargs pylint "$@"
