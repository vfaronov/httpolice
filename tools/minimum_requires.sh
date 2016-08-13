#!/bin/sh

# Install the lowest versions of requirements permitted by HTTPolice,
# so we can ensure that these lower bounds are up-to-date.

set -e

test -e setup.py || { echo 'must run from repo root' >&2; exit 1; }

grep -Eo '[A-Za-z0-9_.]+ >= [A-Za-z0-9_.]+' setup.py | \
    sed -e 's/>=/==/g' >minimum_requirements.txt
pip install -r minimum_requirements.txt
