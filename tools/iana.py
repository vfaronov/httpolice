#!/usr/bin/env python
# -*- coding: utf-8; -*-

"""Tool to synchronize :mod:`httpolice.known` with IANA registries.

Simply run::

  $ tools/iana.py

and it will fetch the protocol elements registered with IANA,
compare them with those in :mod:`httpolice.known`, and report differences.

Items missing from HTTPolice are printed in a format
that can be copy-pasted right into the appropriate module
(run under Python 2, so that strings get the ``u`` prefix for consistency).

If certain items should not be synced, add a ``_no_sync`` key to them.

Items that are present in HTTPolice but not registered with IANA
are **not** reported (there are too many ``X-`` headers that we need to know).

Exits with a non-zero status if any differences have been found.
"""

from __future__ import print_function

import pprint
import re
from six.moves.urllib.parse import urljoin  # pylint: disable=import-error
from six.moves.urllib.request import Request  # pylint: disable=import-error
from six.moves.urllib.request import urlopen  # pylint: disable=import-error
import sys

import lxml.etree

from httpolice.citation import RFC, Citation
import httpolice.known
from httpolice.structure import (AltSvcParam, AuthScheme, CacheDirective,
                                 ContentCoding, FieldName, MediaType, Method,
                                 Preference, RangeUnit, RelationType,
                                 StatusCode, TransferCoding, UpgradeToken,
                                 WarnCode)
from httpolice.util.text import normalize_whitespace


def yes_no(s):
    return {'yes': True, 'no': False}[s]


class Registry(object):

    key_order = []
    xmlns = {'iana': 'http://www.iana.org/assignments'}
    relative_url = None
    cls = None

    def __init__(self, base_url='http://www.iana.org/assignments/'):
        self.base_url = base_url

    def get_all(self):
        tree = self._get_xml(self.relative_url)
        entries = []
        for record in tree.findall('//iana:record', self.xmlns):
            entry = self._from_record(record)
            if entry:
                entries.append(entry)
        return [(self.cls, entries)]

    def _get_xml(self, relative_url):
        req = Request(
            urljoin(self.base_url, relative_url),
            headers={'Accept': 'text/xml, application/xml',
                     'User-Agent': 'HTTPolice-IANA-tool Python-urllib'})
        return lxml.etree.parse(urlopen(req))

    def _from_record(self, record):
        raise NotImplementedError()

    def extract_citations(self, record):
        for xref in record.findall('iana:xref', self.xmlns):
            if xref.get('type') == 'rfc':
                match = re.search(
                    r'RFC(\d+), (Section|Appendix) ([A-Z0-9]+(\.[0-9]+)*)',
                    xref.text or '')
                if match:
                    num = int(match.group(1))
                    kw = match.group(2).lower()
                    sect = RFC.parse_sect(match.group(3))
                    yield RFC(num, **{kw: sect})
                else:
                    num = int(xref.get('data')[3:])
                    yield RFC(num)
            elif xref.get('type') == 'uri':
                title = normalize_whitespace(xref.text) if xref.text else None
                url = xref.get('data')
                yield Citation(title, url)


class HeaderRegistry(Registry):

    cls = FieldName
    relative_url = 'message-headers/message-headers.xml'

    def _from_record(self, record):
        if record.find('iana:protocol', self.xmlns).text != 'http':
            return None
        entry = {
            '_': FieldName(record.find('iana:value', self.xmlns).text),
            '_citations': list(self.extract_citations(record)),
        }
        status = record.find('iana:status', self.xmlns)
        if (status is not None) and status.text:
            entry['iana_status'] = status.text
        return entry


class MethodRegistry(Registry):

    cls = Method
    relative_url = 'http-methods/http-methods.xml'

    def _from_record(self, record):
        return {
            '_': Method(record.find('iana:value', self.xmlns).text),
            '_citations': list(self.extract_citations(record)),
            'safe': yes_no(record.find('iana:safe', self.xmlns).text),
            'idempotent':
                yes_no(record.find('iana:idempotent', self.xmlns).text),
        }


class StatusCodeRegistry(Registry):

    cls = StatusCode
    relative_url = 'http-status-codes/http-status-codes.xml'

    def _from_record(self, record):
        value = record.find('iana:value', self.xmlns).text
        if not value.isdigit():
            return None
        description = record.find('iana:description', self.xmlns).text
        if description.lower() == 'unassigned':
            return None
        return {
            '_': StatusCode(value),
            '_citations': list(self.extract_citations(record)),
            '_title': description,
        }


class ParametersRegistry(Registry):     # pylint: disable=abstract-method

    def get_all(self):
        tree = self._get_xml('http-parameters/http-parameters.xml')
        return [
            (ContentCoding, list(self._content_codings(tree))),
            (Preference, list(self._preferences(tree))),
            (RangeUnit, list(self._range_units(tree))),
            (TransferCoding, list(self._transfer_codings(tree))),
        ]

    def _content_codings(self, tree):
        records = tree.findall(
            '//iana:registry[@id="content-coding"]/iana:record', self.xmlns)
        for record in records:
            yield {
                '_': ContentCoding(
                    record.find('iana:name', self.xmlns).text),
                '_citations': list(self.extract_citations(record)),
            }

    def _preferences(self, tree):
        records = tree.findall(
            '//iana:registry[@id="preferences"]/iana:record', self.xmlns)
        for record in records:
            yield {
                '_': Preference(
                    record.find('iana:name', self.xmlns).text),
                '_citations': list(self.extract_citations(
                    record.find('iana:spec', self.xmlns))),
            }

    def _range_units(self, tree):
        records = tree.findall(
            '//iana:registry[@id="range-units"]/iana:record', self.xmlns)
        for record in records:
            yield {
                '_': RangeUnit(
                    record.find('iana:name', self.xmlns).text),
                '_citations': list(self.extract_citations(record)),
            }

    def _transfer_codings(self, tree):
        records = tree.findall(
            '//iana:registry[@id="transfer-coding"]/iana:record', self.xmlns)
        for record in records:
            yield {
                '_': TransferCoding(
                    record.find('iana:name', self.xmlns).text),
                '_citations': list(self.extract_citations(record)),
            }


class MediaTypeRegistry(Registry):

    cls = MediaType
    relative_url = 'media-types/media-types.xml'

    def _from_record(self, record):
        toplevel = record.getparent().get('id')
        subtype = record.find('iana:name', self.xmlns).text.lower()
        if subtype.startswith('vnd.') or subtype.startswith('prs.'):
            return None
        if len(subtype.split()) > 1:
            if ('deprecated' in subtype) or ('obsoleted' in subtype):
                entry = {'deprecated': True}
                subtype = subtype.split()[0]
            else:
                return None
        else:
            entry = {}
        entry['_'] = MediaType(u'%s/%s' % (toplevel, subtype))
        entry['_citations'] = list(self.extract_citations(record))
        return entry


class UpgradeTokenRegistry(Registry):

    cls = UpgradeToken
    relative_url = 'http-upgrade-tokens/http-upgrade-tokens.xml'

    def _from_record(self, record):
        return {
            '_': UpgradeToken(record.find('iana:value', self.xmlns).text),
            '_citations': list(self.extract_citations(record)),
            '_title':
                record.find('iana:description', self.xmlns).text,
        }


class CacheDirectiveRegistry(Registry):

    cls = CacheDirective
    relative_url = 'http-cache-directives/http-cache-directives.xml'

    def _from_record(self, record):
        return {
            '_': CacheDirective(
                    record.find('iana:value', self.xmlns).text),
            '_citations': list(self.extract_citations(record)),
        }


class WarnCodeRegistry(Registry):

    cls = WarnCode
    relative_url = 'http-warn-codes/http-warn-codes.xml'

    def _from_record(self, record):
        return {
            '_': WarnCode(record.find('iana:value', self.xmlns).text),
            '_citations': list(self.extract_citations(record)),
            '_title': record.find('iana:description', self.xmlns).text,
        }


class AuthSchemeRegistry(Registry):

    cls = AuthScheme
    relative_url = 'http-authschemes/http-authschemes.xml'

    def _from_record(self, record):
        return {
            '_': AuthScheme(record.find('iana:value', self.xmlns).text),
            '_citations': list(self.extract_citations(record)),
        }


class RelationTypeRegistry(Registry):

    cls = RelationType
    relative_url = 'link-relations/link-relations.xml'

    def _from_record(self, record):
        return {
            '_': RelationType(record.find('iana:value', self.xmlns).text),
            '_citations': list(
                self.extract_citations(record.find('iana:spec', self.xmlns))),
        }


class AltSvcParamRegistry(Registry):

    cls = AltSvcParam
    relative_url = 'http-alt-svc-parameters/http-alt-svc-parameters.xml'

    def _from_record(self, record):
        return {
            '_': AltSvcParam(record.find('iana:value', self.xmlns).text),
            '_citations': list(self.extract_citations(record)),
        }


def make_diff(here, there):
    missing = []
    mismatch = []
    for key, entry in there.items():
        if key in here:
            no_sync = here[key].pop('_no_sync', [])
            entry_diff = {k: {'here': here[key].get(k), 'there': v}
                          for k, v in entry.items()
                          if not _info_match(k, here[key].get(k), v) and
                             no_sync != True and k not in no_sync}
            if entry_diff:
                entry_diff['_'] = key
                mismatch.append(entry_diff)
        elif entry['_citations']:
            # We don't have much use for entries without citations.
            missing.append(entry)
    return missing, mismatch


def _info_match(key, here, there):
    if key == '_citations':
        # We consider the citation lists matching if
        # for every citation listed at IANA
        # we have the same citation or a more specific one.
        here = here or []
        for there_cit in there:
            if not any(here_cit.subset_of(there_cit) for here_cit in here):
                return False
        return True
    else:
        return here == there


def main():
    exit_status = 0
    for reg in Registry.__subclasses__():
        for cls, entries in reg().get_all():
            (here, _) = httpolice.known.classes[cls]
            there = {entry['_']: entry for entry in entries}
            missing, mismatch = make_diff(here, there)
            for title, updates in [('missing', missing),
                                   ('mismatch', mismatch)]:
                if updates:
                    print('======== %s %s ========\n' % (cls.__name__, title))
                    pprint.pprint(updates)
                    print('\n')
                    exit_status = 1
    sys.exit(exit_status)


if __name__ == '__main__':
    main()
