# -*- coding: utf-8; -*-

import doctest

import httpolice.util.text


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(httpolice.util.text))
    return tests
