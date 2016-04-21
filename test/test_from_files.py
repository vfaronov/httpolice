# -*- coding: utf-8; -*-

# Treat every file in ``combined_data/`` and ``har_data/`` as a test case.
# Run it through HTTPolice and check the list of resulting notices.
# In combined stream files, the expected notices are specified in the preamble.
# In HAR files, the expected notices are specified in the ``_expected`` key.

import io
import json
import os
import unittest

import six

from httpolice.exchange import check_exchange
from httpolice.inputs.har import har_input
from httpolice.inputs.streams import combined_input, parse_combined
from httpolice.notice import notices
from httpolice.reports import html_report, text_report


class TestFromFiles(unittest.TestCase):

    covered = set()

    def _run_test(self, file_path):
        if file_path.endswith('.har'):
            with io.open(file_path, 'rt', encoding='utf-8-sig') as f:
                expected = sorted(json.load(f)['_expected'])
            exchanges = list(har_input([file_path]))
        else:
            (_, _, _, preamble) = parse_combined(file_path)
            lines = [ln for ln in preamble.splitlines()
                     if not ln.startswith(u'#')]
            line = lines[0]
            expected = sorted(int(n) for n in line.split())
            exchanges = list(combined_input([file_path]))
        for exch in exchanges:
            check_exchange(exch)
        buf = six.BytesIO()
        text_report(exchanges, buf)
        actual = sorted(int(ln[2:6].decode('ascii'))
                        for ln in buf.getvalue().splitlines()
                        if not ln.startswith(b'------------'))
        self.covered.update(actual)
        self.assertEqual(expected, actual)
        html_report(exchanges, six.BytesIO())

    def _make_case(dir_path, name):
        file_path = os.path.join(dir_path, name)
        test_name = name.replace('.', '_')
        def test_func(self):
            self._run_test(file_path)
        return test_name, test_func

    for dir_name in ['combined_data', 'har_data']:
        dir_path = os.path.join(os.path.dirname(__file__), dir_name)
        for name in os.listdir(dir_path):
            test_name, test_func = _make_case(dir_path, name)
            locals()['test_%s' % test_name] = test_func

    def test_all_notices_covered(self):
        self.assertEqual(self.covered, set(notices))
