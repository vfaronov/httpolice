# -*- coding: utf-8; -*-

from collections import namedtuple

import httpolice.common


class FieldName(httpolice.common.CaseInsensitive):

    __slots__ = ()


HeaderField = namedtuple('HeaderField', ('name', 'value'))
