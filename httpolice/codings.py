# -*- coding: utf-8; -*-

"""Decoding content and transfer codings."""

import gzip
import io
import zlib


def decode_gzip(data):
    return gzip.GzipFile(fileobj=io.BytesIO(data)).read()


def decode_deflate(data):
    return zlib.decompress(data)
