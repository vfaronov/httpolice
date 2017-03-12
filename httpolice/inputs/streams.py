# -*- coding: utf-8; -*-

from collections import OrderedDict, namedtuple
from datetime import datetime, timedelta
import io
import itertools
import os
import re

import six

from httpolice.exchange import complaint_box
from httpolice.framing1 import parse_streams
from httpolice.inputs.common import InputError, decode_path
from httpolice.parse import Stream


def streams_input(paths):
    if len(paths) % 2 != 0:
        raise InputError('even number of input streams required')
    pairs = [(paths[i], paths[i + 1], None) for i in range(0, len(paths), 2)]
    return _path_pairs_input(pairs, sniff_direction=False)


def req_stream_input(paths):
    return _path_pairs_input(((path, None, None) for path in paths),
                             sniff_direction=False)


def resp_stream_input(paths):
    return _path_pairs_input(((None, path, None) for path in paths),
                             sniff_direction=False)


def tcpick_input(dir_paths):
    path_pairs = []

    for dir_path in dir_paths:
        # Extract `_StreamInfo` from tcpick filenames so they can be
        # recombined into pairs. This relies on the counter produced by
        # tcpick's ``-F2`` option.
        streams_info = []
        for name in os.listdir(dir_path):
            path = os.path.join(dir_path, name)
            match = re.match(
                r'^tcpick_(\d+)_([^_]+)_([^_]+)_[^.]+.(serv|clnt)\.dat$', name)
            if not match:
                raise InputError('wrong tcpick filename %s '
                                 '(did you use the -F2 option?)' % name)
            (counter, src, dest, direction) = match.groups()
            counter = int(counter)
            if direction == 'serv':
                (src, dest) = (dest, src)
            streams_info.append(_StreamInfo(path, source=src, destination=dest,
                                            connection_hint=counter,
                                            time_hint=None, sort_hint=counter))
        path_pairs.extend(_recombine_streams(streams_info))

    return _path_pairs_input(path_pairs, sniff_direction=True,
                             complain_on_one_sided=True)


def tcpflow_input(dir_paths):
    path_pairs = []

    for dir_path in dir_paths:
        # Extract `_StreamInfo` from tcpflow filenames so they can be
        # recombined into pairs. This relies on the 4-tuple of "source address,
        # source port, destination address, destination port", keeping track
        # of its uniqueness within a given directory.
        # See https://github.com/simsong/tcpflow/issues/128 .
        streams_info = []
        seen = {}
        for name in os.listdir(dir_path):
            if name in ['report.xml', 'alerts.txt']:
                continue
            path = os.path.join(dir_path, name)
            match = re.match(r'^(\d+)-([^-]+-\d+)-([^-]+-\d+)-\d+$', name)
            if not match:
                raise InputError('wrong tcpflow filename %s '
                                 '(did you use the right -T option?)' % name)
            (timestamp, src, dest) = match.groups()
            timestamp = int(timestamp)
            if (src, dest) in seen:
                raise InputError('duplicate source+destination address+port: '
                                 '%s vs. %s' % (path, seen[(src, dest)]))
            seen[(src, dest)] = path
            streams_info.append(_StreamInfo(
                path, source=src, destination=dest, connection_hint=None,
                time_hint=datetime.utcfromtimestamp(timestamp),
                sort_hint=timestamp))
        path_pairs.extend(_recombine_streams(streams_info))

    return _path_pairs_input(path_pairs, sniff_direction=True,
                             complain_on_one_sided=True)


# A `_StreamInfo` instance contains information about one TCP stream --
# that is, data sent by one side of a TCP connection.
_StreamInfo = namedtuple('_StreamInfo', [
    # Path to the file containing the reassembled TCP stream data.
    'path',

    # Opaque strings identifying the source and destination of this stream.
    'source', 'destination',

    # Opaque value to disambiguate different connections between the same
    # source and destination, or `None` if no such value is available.
    'connection_hint',

    # The date and time when this stream started, as a naive UTC `datetime`,
    # or `None` if this information is not available.
    'time_hint',

    # Opaque value (supporting comparisons) that can provide implicit ordering
    # of streams in the absence of both `time_hint` and in-band information.
    'sort_hint',
])


def _recombine_streams(streams_info):
    # Recombine `_StreamInfo` structures into pairs (two-sided connections)
    # and resolve a time hint for each pair, if available.
    # The direction (client/server) for each pair will be resolved
    # later by `_path_pairs_input` (because if that fails, we report a notice,
    # and that can't be done here).
    path_pairs = []

    # Use an `OrderedDict` to preserve implicit ordering given in `sort_hint`.
    streams_map = OrderedDict(
        ((si.connection_hint, si.source, si.destination), si)
        for si in sorted(streams_info, key=lambda si: si.sort_hint))

    while streams_map:
        # pylint: disable=no-member
        (_, stream_info) = streams_map.popitem(last=False)

        # Do we have a corresponding stream file in the reverse direction?
        try:
            other_stream_info = streams_map.pop(
                (stream_info.connection_hint,
                 stream_info.destination, stream_info.source)
            )
        except KeyError:
            other_stream_info = None

        # Resolve a time hint for this connection.
        available_time_hints = [si.time_hint
                                for si in [stream_info, other_stream_info]
                                if si and si.time_hint is not None]
        time_hint = min(available_time_hints) if available_time_hints else None

        path_pairs.append((
            stream_info.path,
            other_stream_info.path if other_stream_info else None,
            time_hint,
        ))

    return path_pairs


def _path_pairs_input(path_pairs, sniff_direction=False,
                      complain_on_one_sided=False):
    sequences = []

    # We have pairs of input files, each corresponding to one TCP connection,
    # and possibly having a time hint indicating when the connection started.
    for (path1, path2, time_hint) in path_pairs:
        sequence = []           # Exchanges from this connection.

        # Some of the pairs may be one-sided, i.e. consisting of
        # only the inbound stream or only the outbound stream.
        # In some cases (``req-stream`` and ``resp-stream`` input formats)
        # this is expected, but in other cases we need to complain.
        # We still want to try and process the one stream though.
        if complain_on_one_sided and (path1 is None or path2 is None):
            sequence.append(complaint_box(1278, path=path1 or path2))

        (inbound_path, outbound_path) = (path1, path2)

        # In some cases (``tcpflow`` and ``tcpick`` input formats)
        # the pairs may not yet be disambiguated as to which side is
        # the inbound (client->server) stream and which is the outbound.
        if sniff_direction:
            direction = _sniff_direction(path1, path2)
            if direction is None:
                # If sniffing fails, this is a non-HTTP/1.x connection
                # that was accidentally captured by tcpflow or something.
                # We don't even try to parse that.
                sequence.append(complaint_box(1279,
                                              path1=path1 or u'(none)',
                                              path2=path2 or u'(none)'))
                (inbound_path, outbound_path) = (None, None)
            else:
                (inbound_path, outbound_path) = direction

        if inbound_path or outbound_path:
            # Finally we can parse the streams as HTTP/1.x,
            # appending them to the complaint boxes we may have produced above.
            sequence = itertools.chain(sequence,
                                       _parse_paths(inbound_path,
                                                    outbound_path))

        sequences.append((iter(sequence), time_hint))

    return _rearrange_by_time(sequences)


def _parse_paths(inbound_path, outbound_path, scheme=u'http'):
    inbound = outbound = None
    if inbound_path is not None:
        with io.open(inbound_path, 'rb') as f:
            inbound = Stream(f.read(), name=decode_path(inbound_path))
    if outbound_path is not None:
        with io.open(outbound_path, 'rb') as f:
            outbound = Stream(f.read(), name=decode_path(outbound_path))
    return parse_streams(inbound, outbound, scheme)


def _rearrange_by_time(sequences):
    # `sequences` is a list of ``(sequence, time_hint)`` pairs.
    # Every `sequence` is an iterator of exchanges from one connection.
    # `time_hint` may be `None` or a naive UTC `datetime` indicating
    # approximately when that connection probably started.

    # What we want to do now is interleave exchanges from different sequences
    # in such a way that exchanges that happened close to each other in time
    # are also close to each other in the output of HTTPolice,
    # even if they happened on different connections.

    # We can't just read all exchanges into one big list and sort it,
    # for two reasons.

    # First, some exchanges may have no metadata indicating time.
    # For example, 5xx responses are allowed to have no Date header.
    # This also applies to the 1278 and 1279 complaint boxes
    # produced by the `_path_pairs_input` function.

    # Second, reading all exchanges eagerly might consume a lot of memory.

    # So instead we carefully walk the sequences based on their time hints.
    # We avoid iterating over a sequence until we know, based on its time hint,
    # that it's likely to provide the next exchange.

    # For every sequence, we keep track of the current position in time
    # and the current exchange.
    position = [(time_hint, None) for (_, time_hint) in sequences]

    while True:
        # Find the sequence with the earliest current position.
        min_i = min_time = None
        for i, x in enumerate(position):
            if x is None:
                # The sequence at this `i` has been exhausted already.
                continue
            (time, _) = x
            if time is None:
                # If a sequence has no time hint, the only way to establish
                # its time of beginning is by looking at the first exchange
                # that has a Date header. So we want to force that now.
                min_i = i
                break
            if min_time is None or time < min_time:
                min_time = time
                min_i = i
        if min_i is None:
            # We have exhausted all sequences.
            break
        i = min_i

        (time, exchange) = position[i]
        if exchange is None:
            # Start iterating over this sequence.
            # Currently (with eager parsing) this means that the stream files
            # for this sequence will be read into memory.
            exchange = next(sequences[i][0])
            new_time = _exchange_time(exchange, time)
            if time is None or new_time > time:
                # So this sequence actually starts at a later time than
                # suggested by its `time_hint` (or the hint is absent),
                # which means that the `min_i` we found above may be wrong.
                # We need to retry.
                position[i] = (new_time, exchange)
                continue

        # OK, this is the next exchange in time order.
        yield exchange

        # Proceed to the next one from this sequence.
        exchange = next(sequences[i][0], None)
        if exchange is None:
            # We're done with this sequence.
            position[i] = None
        else:
            position[i] = (_exchange_time(exchange, time), exchange)


def _exchange_time(exchange, hint):
    # Determine the time at which `exchange` was generated/sent/whatever.
    # Doesn't have to be very precise; the point is to make the report
    # more readable in the common case.
    if exchange.request and exchange.request.headers.date.is_okay:
        return exchange.request.headers.date.value
    for resp in exchange.responses:
        if resp.headers.date.is_okay:
            if resp.headers.age.is_okay:
                return (resp.headers.date.value +
                        timedelta(seconds=resp.headers.age.value))
            else:
                return resp.headers.date.value
    return hint


def _sniff_direction(path1, path2):                 # pragma: no cover
    if path1 and _sniff_outbound(path1):
        return (path2, path1)
    elif path2 and _sniff_outbound(path2):
        return (path1, path2)
    elif path1 and _sniff_inbound(path1):
        return (path1, path2)
    elif path2 and _sniff_inbound(path2):
        return (path2, path1)
    else:
        return None


def _sniff_outbound(path):
    # An outbound HTTP/1.x stream always begins with an HTTP version
    # (of the first response).
    marker = b'HTTP/1.'
    with io.open(path, 'rb') as f:
        return f.read(len(marker)) == marker


def _sniff_inbound(path):
    # An inbound HTTP/1.x stream always contains an HTTP version
    # (of the first request) on the first line, but not at the beginning.
    marker = b'HTTP/1.'
    with io.open(path, 'rb') as f:
        line = f.readline()
    return marker in line and not line.startswith(marker)


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
