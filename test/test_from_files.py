# -*- coding: utf-8; -*-

# Treat every file in ``combined_data/`` as a test case.

import io
import os
import unittest

from six.moves import StringIO

from httpolice.exchange import check_exchange
from httpolice.inputs.streams import combined_input, parse_combined
from httpolice.notice import notices
from httpolice.reports import html_report, text_report
from httpolice.reports.html import render_notice_examples


class TestFromFiles(unittest.TestCase):

    covered = set()
    examples_filename = os.environ.get('WRITE_EXAMPLES_TO')
    examples = {} if examples_filename else None

    def _run_test(self, filename):
        (_, _, _, preamble) = parse_combined(filename)
        lines = [ln for ln in preamble.splitlines() if not ln.startswith(u'#')]
        line = lines[0]
        expected = sorted(int(n) for n in line.split())
        exchanges = list(combined_input([filename]))
        for exch in exchanges:
            check_exchange(exch)
        buf = StringIO()
        text_report(exchanges, buf)
        actual = sorted(int(ln[2:6]) for ln in buf.getvalue().splitlines()
                        if not ln.startswith(u'------------'))
        self.covered.update(actual)
        self.assertEqual(expected, actual)
        html_report(exchanges, StringIO())
        if self.examples is not None:
            for exch in exchanges:
                for ident, ctx in exch.collect_complaints():
                    self.examples.setdefault(ident, ctx)

    def _make_case(data_path, name):
        filename = os.path.join(data_path, name)
        test_name = name.split('.')[0]
        def test_func(self):
            self._run_test(filename)
        return test_name, test_func

    data_path = os.path.join(os.path.dirname(__file__), 'combined_data')
    for name in os.listdir(data_path):
        test_name, test_func = _make_case(data_path, name)
        locals()['test_%s' % test_name] = test_func

    def test_all_notices_covered(self):
        self.assertEqual(self.covered, set(notices))
        if self.examples is not None:
            self.assertEqual(self.covered, set(self.examples))
            with io.open(self.examples_filename, 'wt', encoding='utf-8') as f:
                f.write(render_notice_examples(
                    (notices[ident], ctx)
                    for ident, ctx in sorted(self.examples.items())
                ))
