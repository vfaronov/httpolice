# -*- coding: utf-8; -*-

import calendar
from datetime import date, datetime, time

from httpolice.common import (
    CaseInsensitive,
    Charset,
    ContentCoding,
    MediaType,
    Parametrized,
    ProductName,
    Versioned,
)
from httpolice.parse import (
    ParseError,
    argwrap,
    ci,
    decode,
    function,
    join,
    literal,
    many,
    maybe,
    stringx,
    subst,
    rfc,
    wrap,
)
from httpolice.syntax.common import digit, sp
from httpolice.syntax.rfc4647 import language_range
from httpolice.syntax.rfc7230 import (
    comma_list,
    comma_list1,
    comment,
    ows,
    quoted_string,
    rws,
    token,
)


parameter = (wrap(CaseInsensitive, token) + ~literal('=') +
             (token | decode(quoted_string)))   // rfc(7231, u'parameter')
type_ = token
subtype = token
media_type = argwrap(
    Parametrized,
    wrap(MediaType, join(type_ + '/' + subtype)) +
    many(~(ows + ';' + ows) + parameter))    // rfc(7231, u'media-type')

content_coding = wrap(ContentCoding, token)    // rfc(7231, u'content-coding')

product_version = token
product = argwrap(
    Versioned,
    wrap(ProductName, token) +
    maybe(~literal('/') + product_version))
user_agent = server = argwrap(
    lambda p1, ps: [p1] + ps,
    product + many(~rws + (product | comment)))

day_name = (subst(0, 'Mon') | subst(1, 'Tue') | subst(2, 'Wed') |
            subst(3, 'Thu') | subst(4, 'Fri') | subst(5, 'Sat') |
            subst(6, 'Sun'))

def _to_date(d, m, y):
    try:
        return date(y, m, d)
    except ValueError:
        raise ParseError(u'nonexistent date: %d-%02d-%02d' % (y, m, d))

day = wrap(int, stringx(2, 2, digit))
month = (subst(1, 'Jan') | subst(2, 'Feb') | subst(3, 'Mar') |
         subst(4, 'Apr') | subst(5, 'May') | subst(6, 'Jun') |
         subst(7, 'Jul') | subst(8, 'Aug') | subst(9, 'Sep') |
         subst(10, 'Oct') | subst(11, 'Nov') | subst(12, 'Dec'))
year = wrap(int, stringx(4, 4, digit))
date1 = argwrap(_to_date, day + ~sp + month + ~sp + year)

def _to_time(h, m, s):
    try:
        # This doesn't parse the leap second 23:59:60
        # that is explicitly specified in the RFC.
        # I can ignore this for now.
        # TODO: maybe return 23:59:59 + a debug notice.
        return time(h, m, s)
    except ValueError:
        raise ParseError(u'nonexistent time: %02d:%02d:%02d' % (h, m, s))

hour = wrap(int, stringx(2, 2, digit))
minute = wrap(int, stringx(2, 2, digit))
second = wrap(int, stringx(2, 2, digit))

time_of_day = argwrap(_to_time,
                      hour + ~literal(':') + minute + ~literal(':') + second)

def _to_datetime(dow, d, t):
    return (dow, datetime(d.year, d.month, d.day, t.hour, t.minute, t.second))

imf_fixdate = argwrap(
    _to_datetime,
    day_name + ~(',' + sp) + date1 + ~sp + time_of_day + ~(sp + 'GMT')) \
    // rfc(7231, u'IMF-fixdate')

day_name_l = (subst(0, 'Monday') | subst(1, 'Tuesday') |
              subst(2, 'Wednesday') | subst(3, 'Thursday') |
              subst(4, 'Friday') | subst(5, 'Saturday') | subst(6, 'Sunday'))

date2 = argwrap(
    _to_date,
    day + ~literal('-') + month + ~literal('-') +
    wrap(lambda s: int('19' + s), stringx(2, 2, digit)))

rfc850_date = argwrap(
    _to_datetime,
    day_name_l + ~(',' + sp) + date2 + ~sp + time_of_day + ~(sp + 'GMT'))

date3 = month + ~sp + wrap(int, stringx(2, 2, digit) | (~sp + digit))

asctime_date = argwrap(
    lambda dow, m, d, t, y: _to_datetime(dow, _to_date(d, m, y), t),
    day_name + ~sp + date3 + ~sp + time_of_day + ~sp + year)

def _parse_obs_date(state):
    r = (rfc850_date | asctime_date).parse(state)
    state.complain(1107)
    return r

obs_date = function(_parse_obs_date)   // rfc(7231, u'obs-date')

def _parse_http_date(state):
    claimed_dow, r = (imf_fixdate | obs_date).parse(state)
    if r.weekday() != claimed_dow:
        state.complain(1108, date=r.strftime('%Y-%m-%d'),
                       claimed=calendar.day_name[claimed_dow],
                       actual=calendar.day_name[r.weekday()])
    return r

http_date = function(_parse_http_date)

def _parse_media_range_parameter(state):
    k, v = parameter.parse(state)
    if k == u'q':
        raise ParseError()          # let `accept_params` handle from here on
    return (k, v)

_media_range_parameter = function(_parse_media_range_parameter)

qvalue = wrap(
    float,
    join('0' + maybe(join('.' + stringx(0, 3, digit)), '')) |
    join('1' + maybe(join('.' + stringx(0, 3, '0')), '')))
weight = ~(ows + ';' + ows + ci('q') + '=') + qvalue

media_range = argwrap(
    Parametrized,
    (
        wrap(MediaType, '*/*') |
        wrap(MediaType, join(type_ + '/*')) |
        wrap(MediaType, join(type_ + '/' + subtype))
    ) +
    many(~(ows + ';' + ows) + _media_range_parameter))

accept_ext = (
    ~(ows + ';' + ows) +
     wrap(CaseInsensitive, token) +
     ~literal('=') +
     (token | decode(quoted_string)))
accept_params = argwrap(lambda w, exts: [(CaseInsensitive(u'q'), w)] + exts,
                        weight + many(accept_ext))

accept = comma_list(argwrap(
    Parametrized,
    media_range + maybe(accept_params, [])))

charset = wrap(Charset, token)

accept_charset = comma_list1(argwrap(
    Parametrized,
    (charset | wrap(Charset, '*')) + maybe(weight)))

codings = (
    content_coding |
    wrap(ContentCoding, 'identity') |
    wrap(ContentCoding, '*'))

accept_encoding = comma_list(argwrap(Parametrized, codings + maybe(weight)))

accept_language = comma_list1(argwrap(
    Parametrized,
    language_range + maybe(weight)))
