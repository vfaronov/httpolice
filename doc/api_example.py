import io
import httpolice

exchanges = [
    httpolice.Exchange(
        httpolice.Request(u'https',
                          u'GET', u'/index.html', u'HTTP/1.1',
                          [(u'Host', b'example.com')],
                          b''),
        [
            httpolice.Response(u'HTTP/1.1', 200, u'OK',
                               [(u'Content-Type', b'text/plain')],
                               b'Hello world!'),
        ]
    )
]

ignore_ids = [1089, 1194]         # Errors we don't care about
bad_exchanges = []

for exch in exchanges:
    httpolice.check_exchange(exch)
    if any(notice.severity == httpolice.ERROR and notice.id not in ignore_ids
           for resp in exch.responses       # We only care about responses
           for notice in resp.notices):
        bad_exchanges.append(exch)

if bad_exchanges:
    with io.open('report.html', 'wb') as f:
        httpolice.html_report(bad_exchanges, f)
    print('%d exchanges had problems; report written to file' %
          len(bad_exchanges))
