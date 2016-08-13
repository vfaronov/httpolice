#!/bin/sh

# Whenever we upload to PyPI from the Travis pipeline,
# we also upload the extra docs (as built by ``tools/build_extra_doc.sh``).
# There is currently no way to tell Travis to skip uploading docs --
# https://github.com/travis-ci/dpl/issues/334 .
# However, if we're uploading a development version,
# we don't want to replace the "stable" docs with development ones.
# So we use a hack: download the "stable" files from pythonhosted.org
# in order to upload them back again.

set -e

test -e setup.py || { echo 'must run from repo root' >&2; exit 1; }

if echo "$TRAVIS_TAG" | grep -qF -e .dev -e a -e b -e rc; then
    echo "TRAVIS_TAG=$TRAVIS_TAG seems to be a development version."
    echo "Reverting extra docs to the stable version..."
    cd extra_doc/_build/
    for name in showcase.html notices.html; do
        curl --fail --max-time 20 -O http://pythonhosted.org/HTTPolice/$name
    done
fi
