# -*- coding: utf-8; -*-

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
