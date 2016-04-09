# -*- coding: utf-8; -*-

import codecs
import io
import sys


def stdio_as_text(stream):
    if sys.version_info[0] < 3:
        return codecs.getwriter('utf-8')(stream)
    else:
        return stream


def open_as_text(fn, mode):
    if sys.version_info[0] < 3:
        return codecs.open(fn, mode, 'utf-8')
    else:
        return io.open(fn, mode + 't')
