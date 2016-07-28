# -*- coding: utf-8; -*-

import collections


def duplicates(xs):
    """
    >>> sorted(duplicates([1, 2, 3, 1, 4, 5, 2, 6, 4, 7, 8]))
    [1, 2, 4]
    """
    counter = collections.Counter(xs)
    return [x for (x, count) in counter.items() if count > 1]
