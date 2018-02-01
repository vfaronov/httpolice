# -*- coding: utf-8; -*-

"""Decoding content and transfer codings."""

import zlib

import brotli


def decode_gzip(data):
    # Just ``decompress(data, 16 + zlib.MAX_WBITS)`` doesn't work.
    return zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(data)


def decode_deflate(data):
    return zlib.decompress(data)


def decode_brotli(data):
    return brotli.decompress(data)
