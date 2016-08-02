# -*- coding: utf-8; -*-

import enum


class OrderedEnum(enum.Enum):       # pragma: no cover

    """An ordered variant of :class:`enum.Enum`.

    Taken directly from the `Python docs`__.

    __ https://docs.python.org/3/library/enum.html#orderedenum

    """

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented
