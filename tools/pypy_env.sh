#!/bin/sh

# Travis has an old PyPy version. Install one that is recent enough for us.
# See also https://github.com/travis-ci/travis-ci/issues/5027

set -e

VERSION=pypy2-v5.6.0-linux64
BASE=$HOME/install-pypy

rm -rf "$BASE"
mkdir -p "$BASE"
cd "$BASE"

wget https://bitbucket.org/pypy/pypy/downloads/$VERSION.tar.bz2
tar -jxf $VERSION.tar.bz2
virtualenv --python=$VERSION/bin/pypy env >&2
echo "$PWD/env/bin/activate"
