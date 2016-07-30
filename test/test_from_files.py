# -*- coding: utf-8; -*-

"""File-based test suite.

Treat every file in ``combined_data/`` and ``har_data/`` as a test case.
Run it through HTTPolice and check the list of resulting notices.
In combined stream files, the expected notices are specified in the preamble.
In HAR files, the expected notices are specified in the ``_expected`` key.
"""

import io
import json
import os

import pytest
import six

from httpolice.exchange import check_exchange
from httpolice.inputs.har import har_input
from httpolice.inputs.streams import combined_input, parse_combined
from httpolice.reports import html_report, text_report


base_path = os.path.dirname(__file__)

relative_paths = [os.path.join(section, fn)
                  for section in ['combined_data', 'har_data']
                  for fn in os.listdir(os.path.join(base_path, section))]


@pytest.fixture(params=relative_paths)
def input_from_file(request):
    path = os.path.join(base_path, request.param)
    if path.endswith('.har'):
        with io.open(path, 'rt', encoding='utf-8-sig') as f:
            expected = sorted(json.load(f)['_expected'])
        exchanges = list(har_input([path]))
    else:
        (_, _, _, preamble) = parse_combined(path)
        lines = [ln for ln in preamble.splitlines() if not ln.startswith(u'#')]
        expected = sorted(int(n) for n in lines[0].split())
        exchanges = list(combined_input([path]))
    return (exchanges, expected)


def test_from_file(input_from_file):    # pylint: disable=redefined-outer-name
    (exchanges, expected) = input_from_file
    for exch in exchanges:
        check_exchange(exch)

    buf = six.BytesIO()
    text_report(exchanges, buf)
    actual = sorted(int(ln[2:6])
                    for ln in buf.getvalue().decode('utf-8').splitlines()
                    if not ln.startswith(u'----'))
    assert expected == actual

    html_report(exchanges, six.BytesIO())     # Just check that it doesn't fail
