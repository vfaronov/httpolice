# -*- coding: utf-8; -*-

from httpolice import structure
from httpolice.known.alt_svc_param import known as altsvc
from httpolice.known.auth_scheme import known as auth
from httpolice.known.cache_directive import known as cache
from httpolice.known.content_coding import known as cc
from httpolice.known.header import known as h
from httpolice.known.hsts_directive import known as hsts
from httpolice.known.media_type import known as media
from httpolice.known.method import known as m
from httpolice.known.product import known as prod
from httpolice.known.range_unit import known as unit
from httpolice.known.relation_type import known as rel
from httpolice.known.status_code import known as st
from httpolice.known.transfer_coding import known as tc
from httpolice.known.upgrade_token import known as upgrade
from httpolice.known.warn_code import known as warn

classes = {
    structure.AltSvcParam: altsvc,
    structure.AuthScheme: auth,
    structure.CacheDirective: cache,
    structure.ContentCoding: cc,
    structure.FieldName: h,
    structure.HSTSDirective: hsts,
    structure.MediaType: media,
    structure.Method: m,
    structure.ProductName: prod,
    structure.RangeUnit: unit,
    structure.RelationType: rel,
    structure.StatusCode: st,
    structure.TransferCoding: tc,
    structure.UpgradeToken: upgrade,
    structure.WarnCode: warn,
}


def get_info(obj):
    for cls, known in classes.items():
        if isinstance(obj, cls):
            return known.get_info(obj)


def citation(obj):
    cites = get_info(obj).get('_citations')
    return cites[0] if cites else None


def title(obj, with_citation=False):
    t = get_info(obj).get('_title')
    if with_citation:
        cite = citation(obj)
        if cite and cite.title:
            if t:
                t = u'%s (%s)' % (t, cite.title)
            else:
                t = cite.title
    return t
