# -*- coding: utf-8; -*-

import io

import httpolice.helpers
from httpolice.known import h
import httpolice.notice
import httpolice.reports.html


def test_headers_from_cgi():
    entries = httpolice.helpers.headers_from_cgi({
        'CONTENT_TYPE': 'text/plain',
        'CONTENT_LENGTH': 24,
        'HTTP_HOST': 'example.com',
        'HTTP_USER_AGENT': 'Mozilla/5.0',
        'HTTP_IF_NONE_MATCH': '*',
    })

    assert entries[0][0] == h.host

    assert sorted(entries) == [
        (h.content_length, b'24'),
        (h.content_type, b'text/plain'),
        (h.host, b'example.com'),
        (h.if_none_match, b'*'),
        (h.user_agent, b'Mozilla/5.0'),
    ]


def test_notices_list():
    buf = io.BytesIO()
    httpolice.reports.html.list_notices(buf)
    out = buf.getvalue()
    assert out.count(b'<h3>') == len(httpolice.notice.all_notices)
    assert b'1151' in out
    assert b'Empty list elements in ' in out
    assert b'<var>place</var>' in out
