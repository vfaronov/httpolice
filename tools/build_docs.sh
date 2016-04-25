#!/bin/sh

echo 'Generating notices list...'
python tools/list_notices.py >doc/_build/notices.html || exit 1

echo 'Generating showcase report...'
httpolice -i combined -o html test/combined_data/showcase.https \
    >doc/_build/showcase.html || exit 1

echo 'Checking the API example...'
python doc/api_example.py || exit 1

echo 'Building Sphinx documentation...'
sphinx-build doc/ doc/_build/ || exit 1

echo 'Zipping...'
cd doc/_build/
zip -r doc.zip ./* || exit 1
