# -*- coding: utf-8; -*-

from collections import OrderedDict
import io
import os
import re

import six

from httpolice.exchange import complaint_box
from httpolice.framing1 import parse_streams
from httpolice.inputs.common import InputError, decode_path
from httpolice.parse import Stream


def _path_pairs_input(path_pairs):
    for (inbound_path, outbound_path) in path_pairs:
        inbound = outbound = None
        if inbound_path is not None:
            with io.open(inbound_path, 'rb') as f:
                inbound = Stream(f.read(), name=decode_path(inbound_path))
        if outbound_path is not None:
            with io.open(outbound_path, 'rb') as f:
                outbound = Stream(f.read(), name=decode_path(outbound_path))
        for exch in parse_streams(inbound, outbound, scheme=u'http'):
            yield exch


def streams_input(paths):
    if len(paths) % 2 != 0:
        raise InputError('even number of input streams required')
    for exch in _path_pairs_input((paths[i], paths[i + 1])
                                   for i in range(0, len(paths), 2)):
        yield exch


def req_stream_input(paths):
    for exch in _path_pairs_input((path, None) for path in paths):
        yield exch


def resp_stream_input(paths):
    for exch in _path_pairs_input((None, path) for path in paths):
        yield exch


def tcpick_input(paths):
    for dir_path in paths:
        # Parse tcpick filenames in order to combine them into pairs.
        # We rely on the counter produced by the ``-F2`` option.
        streams_info = []
        for name in os.listdir(dir_path):
            match = re.match(
                r'^tcpick_(\d+)_([^_]+)_([^_]+)_[^.]+.(serv|clnt)\.dat$', name)
            if not match:
                raise InputError('wrong tcpick filename %s '
                                 '(did you use the -F2 option?)' % name)
            (counter, src, dest, direction) = match.groups()
            counter = int(counter)
            if direction == 'serv':
                (src, dest) = (dest, src)
            streams_info.append((counter, counter, src, dest, name))
        for exch in _directory_input(dir_path, streams_info):
            yield exch


def tcpflow_input(paths):
    for dir_path in paths:
        # Parse tcpflow filenames in order to combine them into pairs.
        # We rely on the 4-tuple of
        # "source address, source port, destination address, destination port",
        # keeping track of its uniqueness.
        # See https://github.com/simsong/tcpflow/issues/128 .
        # For sorting, we rely on the timestamp.
        streams_info = []
        seen = {}
        for name in os.listdir(dir_path):
            if name in ['report.xml', 'alerts.txt']:
                continue
            match = re.match(r'^(\d+)-([^-]+-\d+)-([^-]+-\d+)-\d+$', name)
            if not match:
                raise InputError('wrong tcpflow filename %s '
                                 '(did you use the right -T option?)' % name)
            (timestamp, src, dest) = match.groups()
            timestamp = int(timestamp)
            if (src, dest) in seen:
                raise InputError('duplicate source+destination address+port: '
                                 '%s vs. %s' % (name, seen[(src, dest)]))
            seen[(src, dest)] = name
            streams_info.append((timestamp, None, src, dest, name))
        for exch in _directory_input(dir_path, streams_info):
            yield exch


def _directory_input(dir_path, streams_info):
    streams_map = OrderedDict(
        ((conn_key, src, dest), name)
        for (sort_key, conn_key, src, dest, name) in sorted(streams_info))

    while streams_map:
        ((conn_key, src, dest), name) = streams_map.popitem(last=False)
        path = os.path.join(dir_path, name)

        # Do we have a corresponding stream file in the reverse direction?
        try:
            other_name = streams_map.pop((conn_key, dest, src))
        except KeyError:
            other_path = None
            yield complaint_box(1278, path=path)
        else:
            other_path = os.path.join(dir_path, other_name)

        # Which of the two streams is outbound?
        if _sniff_outbound_stream(path):
            pair = (other_path, path)
        elif other_path is None or _sniff_outbound_stream(other_path):
            pair = (path, other_path)
        else:
            yield complaint_box(1279, path=path, other_path=other_path)
            continue

        for exch in _path_pairs_input([pair]):
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
        raise InputError('%s: bad combined file: no inbound marker' % path)
    (preamble, rest) = parts1
    try:
        preamble = preamble.decode('utf-8')
    except UnicodeError as exc:     # pragma: no cover
        six.raise_from(InputError('%s: invalid UTF-8 in preamble' % path), exc)
    parts2 = rest.split(b'======== BEGIN OUTBOUND STREAM ========\r\n', 1)
    if len(parts2) != 2:            # pragma: no cover
        raise InputError('%s: bad combined file: no outbound marker' % path)
    (inbound_data, outbound_data) = parts2

    inbound = Stream(inbound_data, name=decode_path(path) + u' (inbound)')
    outbound = Stream(outbound_data, name=decode_path(path) + u' (outbound)')

    return (inbound, outbound, scheme, preamble)
