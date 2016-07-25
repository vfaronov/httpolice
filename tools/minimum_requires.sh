#!/bin/sh

# Install the lowest versions of requirements permitted by HTTPolice.
# This checks that these lower bounds are up-to-date.

set -e

test -e setup.py || { echo 'must run from repo root' >&2; exit 1; }

sed -e 's/>=/==/g' <requirements.in >minimum_requirements.txt
pip install -r minimum_requirements.txt
