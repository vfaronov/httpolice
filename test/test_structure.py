# -*- coding: utf-8; -*-

import unittest

from httpolice.structure import CaseInsensitive, Parametrized


class TestStructure(unittest.TestCase):

    def test_common_structures(self):
        self.assertEqual(CaseInsensitive(u'foo'), CaseInsensitive(u'Foo'))
        self.assertNotEqual(CaseInsensitive(u'foo'), CaseInsensitive(u'bar'))
        self.assertEqual(CaseInsensitive(u'foo'), u'Foo')
        self.assertNotEqual(CaseInsensitive(u'foo'), u'bar')
        self.assertEqual(Parametrized(CaseInsensitive(u'foo'), []),
                         CaseInsensitive(u'Foo'))
        self.assertEqual(
            Parametrized(CaseInsensitive(u'foo'), [(u'bar', u'qux')]),
            u'Foo')
        self.assertNotEqual(
            Parametrized(CaseInsensitive(u'foo'), [(u'bar', u'qux')]),
            u'bar')
        self.assertEqual(
            Parametrized(CaseInsensitive(u'foo'), [(u'bar', u'qux')]),
            Parametrized(CaseInsensitive(u'Foo'), [(u'bar', u'qux')]))
        self.assertNotEqual(
            Parametrized(CaseInsensitive(u'foo'), [(u'bar', u'qux')]),
            Parametrized(CaseInsensitive(u'foo'), [(u'bar', u'xyzzy')]))
        self.assertNotEqual(
            Parametrized(u'foo', [(u'bar', u'qux')]),
            Parametrized(u'foo', [(u'bar', u'xyzzy')]))
        self.assertNotEqual(
            Parametrized(CaseInsensitive(u'foo'), [(u'bar', u'qux')]),
            Parametrized(CaseInsensitive(u'bar'), [(u'bar', u'qux')]))
