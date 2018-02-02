# -*- coding: utf-8; -*-

from httpolice import Exchange, Request, Response, check_exchange


def test_informational_response_after_final():
    exch = Exchange(
        Request(
            u'https', u'POST', u'/process/', u'HTTP/1.1',
            [
                (u'Host', b'example.com'),
                (u'User-Agent', b'demo'),
                (u'Content-Length', b'14'),
                (u'Content-Type', b'text/plain'),
                (u'Expect', b'100-continue'),
            ],
            b'Hello world!\r\n',
        ),
        [
            Response(
                u'HTTP/1.1', 100, u'Continue', [], b''
            ),
            Response(
                u'HTTP/1.1', 204, u'No Content',
                [(u'Date', b'Fri, 02 Feb 2018 15:44:33 GMT')],
                b'',
            ),
            Response(
                u'HTTP/1.1', 102, u'Processing', [], b''
            ),
        ],
    )
    check_exchange(exch)
    assert [notice.id for notice in exch.request.notices] == []
    assert [notice.id for notice in exch.responses[0].notices] == []
    assert [notice.id for notice in exch.responses[1].notices] == []
    assert [notice.id for notice in exch.responses[2].notices] == [1304]
