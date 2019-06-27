import os

from httpolice.inputs.har import har_input
from httpolice.structure import Unavailable


def load_from_file(name):
    path = os.path.join(os.path.dirname(__file__), 'har_data', name)
    return list(har_input([path]))


def test_request_target_http11():
    [exch] = load_from_file('chrome_text.har')
    # Because this request has a Host header,
    # we use the HTTP/1.x style of request target.
    assert exch.request.target == u'/success.txt'


def test_request_target_http2():
    [exch] = load_from_file('chrome_http2.har')
    # In HTTP/2 requests, Chrome doesn't send the Host header,
    # so we use the full URL as the request target.
    assert exch.request.target == u'https://vasiliy.faronov.name/'


def test_request_text():
    [exch] = load_from_file('firefox_post_form.har')
    assert u'firefox_post_form.har' in exch.request.remark
    assert u'firefox_post_form.har' in exch.responses[0].remark
    # Raw (unencoded) payload body is never available from HAR files.
    assert isinstance(exch.request.body, Unavailable)
    # Nor do we know the encoded payload as a bytestring.
    assert isinstance(exch.request.decoded_body, Unavailable)
    # Only the Unicode text of the body is present here.
    assert exch.request.unicode_body.startswith(u'custname=Vasiliy')


def test_response_fail():
    [exch] = load_from_file('chrome_https_fail.har')
    assert exch.responses == []


def test_response_empty():
    [exch] = load_from_file('firefox_empty.har')
    assert exch.request.body == b''
    assert exch.responses[0].body == b''


def test_response_text():
    [exch] = load_from_file('chrome_text.har')
    assert u'chrome_text.har' in exch.request.remark
    assert u'chrome_text.har' in exch.responses[0].remark
    # Raw (unencoded) payload body is never available from HAR files.
    assert isinstance(exch.responses[0].body, Unavailable)
    # Nor do we know the encoded payload as a bytestring.
    assert isinstance(exch.responses[0].decoded_body, Unavailable)
    # Only the Unicode text of the body is present here.
    assert exch.responses[0].unicode_body == u'success\n'


def test_response_base64():
    exchanges = load_from_file('firefox_gif.har')
    assert exchanges[-2].responses[0].decoded_body.startswith(b'GIF89')


def test_response_bad_base64():
    [exch] = load_from_file('bad_base64.har')
    # Can't do anything with a broken base64 encoding.
    assert isinstance(exch.responses[0].body, Unavailable)
    assert isinstance(exch.responses[0].decoded_body, Unavailable)
    assert isinstance(exch.responses[0].unicode_body, Unavailable)


def test_fiddler_connect():
    exchanges = load_from_file('fiddler+ie11_connect.har')
    assert u'fiddler+ie11_connect.har' in exchanges[0].request.remark
    assert u'fiddler+ie11_connect.har' in exchanges[0].responses[0].remark
    assert exchanges[0].request.target == u'httpbin.org:443'
    assert exchanges[0].request.body == b''
    assert exchanges[0].request.decoded_body == b''
    assert exchanges[0].responses[0].headers[u'StartTime'].is_present
    assert exchanges[0].responses[0].headers[u'EndTime'].is_absent
    assert exchanges[0].responses[0].body == b''
    assert exchanges[0].responses[0].decoded_body == b''


def test_firefox_304():
    # Firefox includes content on 304 responses, but we ignore it.
    [exch, _] = load_from_file('firefox_304.har')
    assert exch.responses[0].body == b''
    assert exch.responses[0].decoded_body == b''
    assert exch.responses[0].unicode_body == u''
