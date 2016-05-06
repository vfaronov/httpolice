# -*- coding: utf-8; -*-

"""Input formats for HTTPolice (mainly for the command-line tool).

Every input format is implemented as a function with the following interface:

- it accepts a list of paths (to files or directories, depends on the format);
- it returns an iterable of :class:`~httpolice.Exchange`;
- it may raise :exc:`InputError` on fatal errors;
- it may pass through :exc:`EnvironmentError` on errors like invalid paths;
- it may yield empty exchanges (containing only notices) on non-fatal errors.
"""

from httpolice.inputs.common import InputError
from httpolice.inputs.har import har_input
from httpolice.inputs.streams import (
    combined_input,
    req_stream_input,
    resp_stream_input,
    streams_input,
    tcpflow_input,
    tcpick_input,
)


formats = {
    u'streams': streams_input,
    u'req-stream': req_stream_input,
    u'resp-stream': resp_stream_input,
    u'tcpick': tcpick_input,
    u'tcpflow': tcpflow_input,
    u'combined': combined_input,
    u'har': har_input,
}
