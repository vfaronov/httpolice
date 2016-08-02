#!/bin/sh

set -e

test -e setup.py || { echo 'must run from repo root' >&2; exit 1; }

py.test --cov=httpolice/ --cov=test/ --cov-fail-under=100 --cov-report=html
