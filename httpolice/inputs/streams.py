# -*- coding: utf-8; -*-

from collections import OrderedDict
import io
import os
import re

from httpolice.framing1 import parse_streams


def streams_input(paths):
    if len(paths) % 2 != 0:
        raise RuntimeError('even number of input files required')
    while paths:
        with io.open(paths.pop(0), 'rb') as f:
            inbound_data = f.read()
        with io.open(paths.pop(0), 'rb') as f:
            outbound_data = f.read()
        for exch in parse_streams(inbound_data, outbound_data, scheme=u'http'):
            yield exch


def req_stream_input(paths):
    while paths:
        with io.open(paths.pop(0), 'rb') as f:
            data = f.read()
        for exch in parse_streams(data, None, scheme=u'http'):
            yield exch


def resp_stream_input(paths):
    while paths:
        with io.open(paths.pop(0), 'rb') as f:
            data = f.read()
        for exch in parse_streams(None, data, scheme=u'http'):
            yield exch


def tcpick_input(paths):
    for dir_path in paths:
        # Parse tcpick filenames in order to combine them into pairs.
        streams_info = []
        for name in os.listdir(dir_path):
            path = os.path.join(dir_path, name)
            match = re.match(
                r'^tcpick_([^_]+)_([^_]+)_([^.]+).(serv|clnt)(\.[^.]+)?\.dat$',
                name)
            if not match:
                continue
            (src, dest, port, direction, counter) = match.groups()
            counter = counter or ''
            sort_key = (os.stat(path).st_ctime, counter)
            conn_key = (port, counter)
            if direction == 'serv':
                (src, dest) = (dest, src)
            streams_info.append((sort_key, conn_key, src, dest, name))
        for exch in _directory_input(dir_path, streams_info):
            yield exch


def tcpflow_input(paths):
    for dir_path in paths:
        # Parse tcpflow filenames in order to combine them into pairs.
        streams_info = []
        for name in os.listdir(dir_path):
            match = re.match(r'^(\d+)-(\d+)-([^-]+)-([^-]+)$', name)
            if not match:
                continue
            (timestamp, counter, src, dest) = match.groups()
            timestamp = int(timestamp)
            counter = int(counter)
            sort_key = (timestamp, counter)
            conn_key = counter
            streams_info.append((sort_key, conn_key, src, dest, name))
        for exch in _directory_input(dir_path, streams_info):
            yield exch


def _directory_input(dir_path, streams_info):
    streams_map = OrderedDict(
        ((conn_key, src, dest), name)
        for (sort_key, conn_key, src, dest, name) in sorted(streams_info)
        if sort_key is not None)
    paired_paths = []

    while streams_map:
        ((conn_key, src, dest), name) = streams_map.popitem(last=False)
        path = os.path.join(dir_path, name)

        # Do we have a corresponding stream file in the reverse direction?
        try:
            other_name = streams_map[(conn_key, dest, src)]
        except KeyError:
            raise RuntimeError('no reverse stream corresponding to %s' % path)

        other_path = os.path.join(dir_path, other_name)
        del streams_map[(conn_key, dest, src)]

        # Which of the two streams is outbound?
        if _sniff_outbound_stream(path):
            paired_paths.extend((other_path, path))
        elif _sniff_outbound_stream(other_path):
            paired_paths.extend((path, other_path))
        else:
            raise RuntimeError(
                'cannot detect streams direction (not HTTP/1.x?): %s and %s' %
                (path, other_path))

    for exch in streams_input(paired_paths):
        yield exch


def _sniff_outbound_stream(path):
    # An outbound HTTP/1.x stream always begins with
    # the HTTP version (of the first response).
    with io.open(path, 'rb') as f:
        return f.read(5) == b'HTTP/'


def combined_input(paths):
    for path in paths:
        (inbound, outbound, scheme, _) = parse_combined(path)
        for exch in parse_streams(inbound, outbound, scheme):
            yield exch


def parse_combined(path):
    if path.endswith('.https'):
        scheme = u'https'
    elif path.endswith('.noscheme'):
        scheme = None
    else:
        scheme = u'http'

    with io.open(path, 'rb') as f:
        data = f.read()
    parts1 = data.split(b'======== BEGIN INBOUND STREAM ========\r\n', 1)
    if len(parts1) != 2:
        raise RuntimeError('bad combined file: no inbound marker: %s' % path)
    (preamble, rest) = parts1
    preamble = preamble.decode('utf-8')
    parts2 = rest.split(b'======== BEGIN OUTBOUND STREAM ========\r\n', 1)
    if len(parts2) != 2:
        raise RuntimeError('bad combined file: no outbound marker: %s' % path)
    (inbound, outbound) = parts2

    return (inbound, outbound, scheme, preamble)
