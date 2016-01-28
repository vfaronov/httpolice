# -*- coding: utf-8; -*-

import urlnorm


def url_equals(url1, url2):
    try:
        return urlnorm.norm(url1) == urlnorm.norm(url2)
    except urlnorm.InvalidUrl:
        return False
