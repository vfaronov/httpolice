# -*- coding: utf-8; -*-

from datetime import date, datetime, time

from httpolice.citation import RFC
from httpolice.parse import (auto, can_complain, fill_names, literal, many,
                             maybe, maybe_str, named, octet, pivot, skip,
                             string1, string_times, subst)
from httpolice.structure import (CaseInsensitive, Charset, ContentCoding,
                                 MediaType, MultiDict, Parametrized,
                                 ProductName, Unavailable, Versioned)
from httpolice.syntax.common import DIGIT, SP
from httpolice.syntax.rfc3986 import URI_reference, absolute_URI
from httpolice.syntax.rfc4647 import language_range
from httpolice.syntax.rfc5646 import Language_Tag as language_tag
from httpolice.syntax.rfc7230 import (OWS, RWS, comma_list, comma_list1,
                                      comment, field_name, method, partial_URI,
                                      quoted_string, token, token__excluding)


# The standard library's `calendar.day_name` is locale-dependent,
# which brings in Unicode problems.
_DAY_NAMES = [u'Monday', u'Tuesday', u'Wednesday', u'Thursday', u'Friday',
              u'Saturady', u'Sunday']


_BAD_MEDIA_TYPES = {
    MediaType(u'plain/text'): MediaType(u'text/plain'),
    MediaType(u'text/json'): MediaType(u'application/json'),
}

@can_complain
def _check_media_type(complain, mtype):
    if mtype in _BAD_MEDIA_TYPES:
        complain(1282, bad=mtype, good=_BAD_MEDIA_TYPES[mtype])
    return mtype


def parameter(exclude=None, name_cls=CaseInsensitive):
    return (
        (name_cls << token__excluding(exclude or [])) *
        skip('=') * (token | quoted_string)
    ) > named(u'parameter', RFC(7231), is_pivot=True)

type_ = token                                                           > pivot
subtype = token                                                         > pivot
media_type = Parametrized << (
    (_check_media_type << (MediaType << type_ + '/' + subtype)) *
    (MultiDict << many(skip(OWS * ';' * OWS) * parameter())))           > pivot

content_coding = ContentCoding << token                                 > pivot

product_version = token                                                 > pivot
product = Versioned << ((ProductName << token) *
                        maybe(skip('/') * product_version))             > pivot
User_Agent = product % many(skip(RWS) *
                            (product | comment(include_parens=False)))  > pivot
Server = product % many(skip(RWS) *
                        (product | comment(include_parens=False)))      > pivot

day_name = (subst(0) << octet(0x4D) * octet(0x6F) * octet(0x6E) |
            subst(1) << octet(0x54) * octet(0x75) * octet(0x65) |
            subst(2) << octet(0x57) * octet(0x65) * octet(0x64) |
            subst(3) << octet(0x54) * octet(0x68) * octet(0x75) |
            subst(4) << octet(0x46) * octet(0x72) * octet(0x69) |
            subst(5) << octet(0x53) * octet(0x61) * octet(0x74) |
            subst(6) << octet(0x53) * octet(0x75) * octet(0x6E))        > pivot

@can_complain
def _to_date(complain, d, m, y):
    try:
        return date(y, m, d)
    except ValueError:
        complain(1222, date=u'%d-%02d-%02d' % (y, m, d))
        return Unavailable

day = int << string_times(2, 2, DIGIT)                                  > pivot
month = (subst(1) << octet(0x4A) * octet(0x61) * octet(0x6E)  |
         subst(2) << octet(0x46) * octet(0x65) * octet(0x62)  |
         subst(3) << octet(0x4D) * octet(0x61) * octet(0x72)  |
         subst(4) << octet(0x41) * octet(0x70) * octet(0x72)  |
         subst(5) << octet(0x4D) * octet(0x61) * octet(0x79)  |
         subst(6) << octet(0x4A) * octet(0x75) * octet(0x6E)  |
         subst(7) << octet(0x4A) * octet(0x75) * octet(0x6C)  |
         subst(8) << octet(0x41) * octet(0x75) * octet(0x67)  |
         subst(9) << octet(0x53) * octet(0x65) * octet(0x70)  |
         subst(10) << octet(0x4F) * octet(0x63) * octet(0x74) |
         subst(11) << octet(0x4E) * octet(0x6F) * octet(0x76) |
         subst(12) << octet(0x44) * octet(0x65) * octet(0x63))          > pivot
year = int << string_times(4, 4, DIGIT)                                 > pivot

date1 = _to_date << day * skip(SP) * month * skip(SP) * year            > pivot

@can_complain
def _to_time(complain, h, m, s):
    try:
        # This doesn't parse the leap second 23:59:60
        # that is explicitly specified in the RFC.
        # I can ignore this for now.
        return time(h, m, s)
    except ValueError:
        complain(1223, time=u'%02d:%02d:%02d' % (h, m, s))
        return Unavailable

hour = int << string_times(2, 2, DIGIT)                                 > pivot
minute = int << string_times(2, 2, DIGIT)                               > pivot
second = int << string_times(2, 2, DIGIT)                               > pivot

time_of_day = _to_time << (hour * skip(':') *
                           minute * skip(':') *
                           second)                                      > pivot

def _to_datetime(dow, d, t):
    if d is Unavailable or t is Unavailable:
        return (dow, Unavailable)
    else:
        return (dow, datetime(d.year, d.month, d.day,
                              t.hour, t.minute, t.second))

GMT = octet(0x47) * octet(0x4D) * octet(0x54)                           > auto
IMF_fixdate = _to_datetime << (day_name * skip(',' * SP) *
                               date1 * skip(SP) *
                               time_of_day * skip(SP * GMT))            > pivot

day_name_l = (
    subst(0) << (octet(0x4D) * octet(0x6F) * octet(0x6E) * octet(0x64) *
                 octet(0x61) * octet(0x79)) |
    subst(1) << (octet(0x54) * octet(0x75) * octet(0x65) * octet(0x73) *
                 octet(0x64) * octet(0x61) * octet(0x79)) |
    subst(2) << (octet(0x57) * octet(0x65) * octet(0x64) * octet(0x6E) *
                 octet(0x65) * octet(0x73) * octet(0x64) * octet(0x61) *
                 octet(0x79)) |
    subst(3) << (octet(0x54) * octet(0x68) * octet(0x75) * octet(0x72) *
                 octet(0x73) * octet(0x64) * octet(0x61) * octet(0x79)) |
    subst(4) << (octet(0x46) * octet(0x72) * octet(0x69) * octet(0x64) *
                 octet(0x61) * octet(0x79)) |
    subst(5) << (octet(0x53) * octet(0x61) * octet(0x74) * octet(0x75) *
                 octet(0x72) * octet(0x64) * octet(0x61) * octet(0x79)) |
    subst(6) << (octet(0x53) * octet(0x75) * octet(0x6E) * octet(0x64) *
                 octet(0x61) * octet(0x79))
)                                                                       > pivot

date2 = _to_date << (
    day * skip('-') *
    month * skip('-') *
    ((lambda s: int('19' + s)) << string_times(2, 2, DIGIT)))           > pivot

rfc850_date = _to_datetime << (day_name_l * skip(',' * SP) *
                               date2 * skip(SP) *
                               time_of_day * skip(SP * GMT))            > pivot

date3 = month * skip(SP) * (int << string_times(2, 2, DIGIT) |
                            int << skip(SP) * DIGIT)                    > pivot

@can_complain
def _from_asctime(complain, dow, dm, t, y):
    (m, d) = dm
    return _to_datetime(dow, _to_date(complain, d, m, y), t)

asctime_date = _from_asctime << (day_name * skip(SP) *
                                 date3 * skip(SP) *
                                 time_of_day * skip(SP) *
                                 year)                                  > pivot

@can_complain
def _obsolete_date(complain, r):
    complain(1107)
    return r

obs_date = (_obsolete_date << rfc850_date |
            _obsolete_date << asctime_date)                             > pivot

@can_complain
def _check_day_of_week(complain, r):
    (claimed_dow, r) = r
    if r is not Unavailable and r.weekday() != claimed_dow:
        complain(1108, date=r.strftime(u'%Y-%m-%d'),
                 claimed=_DAY_NAMES[claimed_dow],
                 actual=_DAY_NAMES[r.weekday()])
    return r

HTTP_date = (_check_day_of_week << IMF_fixdate |
             _check_day_of_week << obs_date)                            > pivot

def media_range(no_q=False):
    return Parametrized << (
        (
            literal('*/*') |
            type_ + '/' + '*' |
            _check_media_type << (MediaType << type_ + '/' + subtype)
        ) *
        (
            MultiDict << many(
                skip(OWS * ';' * OWS) *
                parameter(exclude=['q'] if no_q else [])
            )
        )
    ) > named(u'media-range', RFC(7231), is_pivot=True)

qvalue = (float << '0' + maybe_str('.' + string_times(0, 3, DIGIT)) |
          float << '1' + maybe_str('.' + string_times(0, 3, '0')))      > pivot
weight = skip(OWS * ';' * OWS * 'q=') * qvalue                          > pivot
accept_ext = (skip(OWS * ';' * OWS) * token *
              maybe(skip('=') * (token | quoted_string)))               > pivot

def _prepend_q(q, xs):
    return MultiDict([(CaseInsensitive(u'q'), q)] + xs)

accept_params = _prepend_q << weight * many(accept_ext)                 > pivot

Accept = comma_list(
    Parametrized << (media_range(no_q=True) *
                     maybe(accept_params, MultiDict())))                > pivot

charset = Charset << token                                              > pivot
Accept_Charset = comma_list1(
    Parametrized << ((charset | Charset << literal('*')) *
                     maybe(weight)))                                    > pivot

codings = (content_coding |
           ContentCoding << literal('identity') |
           literal('*'))                                                > pivot
Accept_Encoding = comma_list(Parametrized << codings * maybe(weight))   > pivot

Accept_Language = comma_list1(
    Parametrized << language_range * maybe(weight))                     > pivot

delay_seconds = int << string1(DIGIT)                                   > pivot
Retry_After = HTTP_date | delay_seconds                                 > pivot

Allow = comma_list(method)                                              > pivot
Content_Encoding = comma_list1(content_coding)                          > pivot
Content_Language = comma_list1(language_tag)                            > pivot
Content_Location = absolute_URI | partial_URI                           > pivot
Content_Type = media_type                                               > pivot
Date = HTTP_date                                                        > pivot
Location = URI_reference                                                > pivot
Max_Forwards = int << string1(DIGIT)                                    > pivot
Referer = absolute_URI | partial_URI                                    > pivot
Vary = '*' | comma_list1(field_name)                                    > pivot
Expect = CaseInsensitive << literal('100-continue')                     > pivot

fill_names(globals(), RFC(7231))
