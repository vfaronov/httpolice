# -*- coding: utf-8; -*-

import pprint
import re
import urllib2
import urlparse

import lxml.etree

from httpolice.citation import Citation, RFC
import httpolice.known
from httpolice.structure import (
    AuthScheme,
    CacheDirective,
    ContentCoding,
    FieldName,
    MediaType,
    Method,
    RangeUnit,
    RelationType,
    StatusCode,
    TransferCoding,
    UpgradeToken,
    WarnCode,
)


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
        req = urllib2.Request(
            urlparse.urljoin(self.base_url, relative_url),
            headers={'Accept': 'text/xml, application/xml',
                     'User-Agent': 'HTTPolice-IANA-tool Python-urllib'})
        return lxml.etree.parse(urllib2.urlopen(req))

    def _from_record(self, record):
        raise NotImplementedError()

    def extract_citations(self, record):
        for xref in record.findall('iana:xref', self.xmlns):
            if xref.get('type') == 'rfc':
                match = re.match(
                    r'RFC(\d+), (Section|Appendix) ([A-Z0-9]+(\.[0-9]+)*)',
                    xref.text or '')
                if match:
                    num = int(match.group(1))
                    kw = match.group(2).lower()
                    sect = tuple(int(n) if n.isdigit() else n
                                 for n in match.group(3).split('.'))
                    yield RFC(num, **{kw: sect})
                else:
                    num = int(xref.get('data')[3:])
                    yield RFC(num)
            elif xref.get('type') == 'uri':
                yield Citation(xref.text, xref.get('data'))


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


class ParametersRegistry(Registry):

    def get_all(self):
        tree = self._get_xml('http-parameters/http-parameters.xml')
        return [
            (ContentCoding, list(self._content_codings(tree))),
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


def make_diff(here, there):
    not_here, mismatch, not_there = [], [], []
    for key, entry in there.items():
        if key in here:
            entry_diff = {k: {'here': here[key].get(k), 'there': v}
                          for k, v in entry.items()
                          if not _info_match(k, here[key].get(k), v)}
            if entry_diff:
                entry_diff['_'] = key
                mismatch.append(entry_diff)
        elif entry['_citations']:
            # We don't have much use for entries without citations.
            not_here.append(entry)
    for key in set(here) - set(there):
        not_there.append(here[key])
    return not_here, mismatch, not_there


def _info_match(key, here, there):
    if key == '_citations':
        # We consider the citation lists matching if
        # for every citation listed at IANA
        # we have the same citation or a more specific one.
        for there_cit in there:
            if not any(here_cit.subset_of(there_cit) for here_cit in here):
                return False
        return True
    else:
        return here == there


def main():
    for reg in Registry.__subclasses__():
        for cls, entries in reg().get_all():
            here = httpolice.known.classes[cls]
            there = {entry['_']: entry for entry in entries}
            not_here, mismatch, not_there = make_diff(here, there)
            for title, updates in [('not here', not_here),
                                   ('mismatch', mismatch),
                                   ('not there', not_there)]:
                if updates:
                    print '======== %s %s ========\n' % (cls.__name__, title)
                    pprint.pprint(updates)
                    print '\n'


if __name__ == '__main__':
    main()
