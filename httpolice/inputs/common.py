# -*- coding: utf-8; -*-

import sys


class InputError(Exception):

    pass


fs_encoding = sys.getfilesystemencoding()

def decode_path(path):     # pragma: no cover
    if isinstance(path, bytes):
        return path.decode(fs_encoding, 'replace')
    else:
        return path
