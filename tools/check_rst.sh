#!/bin/bash

set -e

test -e setup.py || { echo 'must run from repo root' >&2; exit 1; }

for fn in *.rst; do
    rst2html.py --halt=warning "$fn" >/dev/null
done
