#!/usr/bin/env python
# -*- coding: utf-8; -*-

"""Tool to synchronize :mod:`httpolice.known` with IANA registries.

Simply run::

  $ tools/iana.py

and it will fetch the protocol elements registered with IANA,
compare them with those in :mod:`httpolice.known`, and dump updates
back into CSV files. Then just use your favorite ``git difftool -d``
to check that the updates make sense, and ``git commit`` them.

Doesn't work under Python 2 because trying to marry CSV, Unicode, and newlines
across Python 2 and 3 is too much for me.

This only updates existing entries and adds new ones. Entries that are present
in HTTPolice but not registered with IANA are not touched (there are too many
``X-`` headers that we need to know).

You can prevent updating certain entries by filling out their ``no_sync`` field
with a comma-separated list of "processed" fields to skip, such as
``citation,title``, or an asterisk ``*`` to entirely skip the entry.

"""

import re
from six.moves.urllib.parse import urljoin  # pylint: disable=import-error
from six.moves.urllib.request import Request  # pylint: disable=import-error
from six.moves.urllib.request import urlopen  # pylint: disable=import-error

import lxml.etree

from httpolice import known
from httpolice.citation import RFC, Citation
from httpolice.structure import (AltSvcParam, AuthScheme, CacheDirective,
                                 ContentCoding, FieldName, ForwardedParam,
                                 MediaType, Method, Preference, RangeUnit,
                                 RelationType, StatusCode, TransferCoding,
                                 UpgradeToken, WarnCode)
from httpolice.util.text import normalize_whitespace


def yes_no(s):
    return {'yes': True, 'no': False}[s]


class Registry(object):

    key_order = []
    xmlns = {'iana': 'http://www.iana.org/assignments'}
    relative_url = None
    registry_id = None
    cls = None

    def __init__(self, base_url='http://www.iana.org/assignments/'):
        self.base_url = base_url

    def get_all(self):
        tree = self._get_xml(self.relative_url)
        entries = []
        if self.registry_id:
            xpath = '//iana:registry[@id="%s"]/iana:record' % self.registry_id
        else:
            xpath = '//iana:record'
        for record in tree.findall(xpath, self.xmlns):
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

    def extract_citation(self, record):
        for xref in record.findall('iana:xref', self.xmlns):
            if xref.get('type') == 'rfc':
                match = re.search(
                    r'RFC(\d+), (Section|Appendix) ([A-Z0-9]+(\.[0-9]+)*)',
                    xref.text or '')
                if match:
                    num = int(match.group(1))
                    kw = match.group(2).lower()
                    sect = match.group(3)
                    return RFC(num, **{kw: sect})
                else:
                    num = int(xref.get('data')[3:])
                    return RFC(num)
            elif xref.get('type') == 'uri':
                title = normalize_whitespace(xref.text) if xref.text else None
                url = xref.get('data')
                return Citation(title, url)
        return None


class HeaderRegistry(Registry):

    cls = FieldName
    relative_url = 'message-headers/message-headers.xml'

    def _from_record(self, record):
        if record.find('iana:protocol', self.xmlns).text != 'http':
            return None
        entry = {
            'key': FieldName(record.find('iana:value', self.xmlns).text),
            'citation': self.extract_citation(record),
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
            'key': Method(record.find('iana:value', self.xmlns).text),
            'citation': self.extract_citation(record),
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
            'key': StatusCode(value),
            'citation': self.extract_citation(record),
            'title': description,
        }


class ParametersRegistry(Registry):     # pylint: disable=abstract-method

    def get_all(self):
        tree = self._get_xml('http-parameters/http-parameters.xml')
        return [
            (ContentCoding, list(self._content_codings(tree))),
            (ForwardedParam, list(self._forwarded_parameters(tree))),
            (Preference, list(self._preferences(tree))),
            (RangeUnit, list(self._range_units(tree))),
            (TransferCoding, list(self._transfer_codings(tree))),
        ]

    def _content_codings(self, tree):
        records = tree.findall(
            '//iana:registry[@id="content-coding"]/iana:record', self.xmlns)
        for record in records:
            yield {
                'key': ContentCoding(
                    record.find('iana:name', self.xmlns).text),
                'citation': self.extract_citation(record),
            }

    def _forwarded_parameters(self, tree):
        records = tree.findall(
            '//iana:registry[@id="forwarded"]/iana:record', self.xmlns)
        for record in records:
            yield {
                'key': ForwardedParam(
                    record.find('iana:name', self.xmlns).text),
                'citation': self.extract_citation(record),
                'description':
                    record.find('iana:description', self.xmlns).text,
            }

    def _preferences(self, tree):
        records = tree.findall(
            '//iana:registry[@id="preferences"]/iana:record', self.xmlns)
        for record in records:
            yield {
                'key': Preference(
                    record.find('iana:name', self.xmlns).text),
                'citation': self.extract_citation(
                    record.find('iana:spec', self.xmlns)),
            }

    def _range_units(self, tree):
        records = tree.findall(
            '//iana:registry[@id="range-units"]/iana:record', self.xmlns)
        for record in records:
            yield {
                'key': RangeUnit(
                    record.find('iana:name', self.xmlns).text),
                'citation': self.extract_citation(record),
            }

    def _transfer_codings(self, tree):
        records = tree.findall(
            '//iana:registry[@id="transfer-coding"]/iana:record', self.xmlns)
        for record in records:
            yield {
                'key': TransferCoding(
                    record.find('iana:name', self.xmlns).text),
                'citation': self.extract_citation(record),
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
        entry['key'] = MediaType(u'%s/%s' % (toplevel, subtype))
        entry['citation'] = self.extract_citation(record)
        return entry


class UpgradeTokenRegistry(Registry):

    cls = UpgradeToken
    relative_url = 'http-upgrade-tokens/http-upgrade-tokens.xml'

    def _from_record(self, record):
        return {
            'key': UpgradeToken(record.find('iana:value', self.xmlns).text),
            'citation': self.extract_citation(record),
            'title':
                record.find('iana:description', self.xmlns).text,
        }


class CacheDirectiveRegistry(Registry):

    cls = CacheDirective
    relative_url = 'http-cache-directives/http-cache-directives.xml'

    def _from_record(self, record):
        return {
            'key': CacheDirective(record.find('iana:value', self.xmlns).text),
            'citation': self.extract_citation(record),
        }


class WarnCodeRegistry(Registry):

    cls = WarnCode
    relative_url = 'http-warn-codes/http-warn-codes.xml'

    def _from_record(self, record):
        return {
            'key': WarnCode(record.find('iana:value', self.xmlns).text),
            'citation': self.extract_citation(record),
            'title': record.find('iana:description', self.xmlns).text,
        }


class AuthSchemeRegistry(Registry):

    cls = AuthScheme
    relative_url = 'http-authschemes/http-authschemes.xml'
    registry_id = 'authschemes'

    def _from_record(self, record):
        return {
            'key': AuthScheme(record.find('iana:value', self.xmlns).text),
            'citation': self.extract_citation(record),
        }


class RelationTypeRegistry(Registry):

    cls = RelationType
    relative_url = 'link-relations/link-relations.xml'

    def _from_record(self, record):
        return {
            'key': RelationType(record.find('iana:value', self.xmlns).text),
            'citation': 
                self.extract_citation(record.find('iana:spec', self.xmlns)),
        }


class AltSvcParamRegistry(Registry):

    cls = AltSvcParam
    relative_url = 'http-alt-svc-parameters/http-alt-svc-parameters.xml'

    def _from_record(self, record):
        return {
            'key': AltSvcParam(record.find('iana:value', self.xmlns).text),
            'citation': self.extract_citation(record),
        }


def dump_updates(knowledge, their_entries):
    entries = {key: knowledge.get(key).copy() for key in knowledge}

    for their in their_entries:
        key = their['key']
        entry = entries.setdefault(key, {})
        no_sync = entry.get('no_sync', '').split(',')
        entry.update({
            k: v for (k, v) in their.items()
            if v is not None and k not in no_sync and '*' not in no_sync
            and not (k == 'citation' and k in entry and entry[k].subset_of(v))
        })
        if not entry.get('citation') and key not in knowledge:
            # This entry was newly fetched from IANA, but has no citations
            # (e.g. there are many such media types). These are mostly useless.
            del entries[key]

    knowledge.dump(entry for (_, entry) in sorted(entries.items()))


def main():
    for reg in Registry.__subclasses__():
        for cls, entries in reg().get_all():
            (knowledge, _) = known.classes[cls]
            dump_updates(knowledge, entries)


if __name__ == '__main__':
    main()
