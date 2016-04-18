# -*- coding: utf-8; -*-

def pop_pseudo_headers(entries):
    # Pseudo-headers, as used in HTTP/2 and SPDY (?),
    # are explicitly not HTTP headers (see RFC 7540),
    # but they are included in the headers exported
    # by Chrome (in HAR) and mitmproxy.
    i = 0
    r = {}
    while i < len(entries):
        (name, value) = entries[i]
        if name.startswith(u':'):
            r[name] = value
            del entries[i]
        else:
            i += 1
    return r
