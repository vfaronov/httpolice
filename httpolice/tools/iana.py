# -*- coding: utf-8; -*-

import re
import urllib2
import urlparse

import lxml.etree

from httpolice.common import (
    Citation,
    FieldName,
    MediaType,
    Method,
    StatusCode,
    RFC,
    TransferCoding,
)
from httpolice.known import h, m, media, st, tc


def yes_no(s):
    return {'yes': True, 'no': False}[s]


class Registry(object):

    key_order = []
    xmlns = {'iana': 'http://www.iana.org/assignments'}

    def __init__(self, base_url='http://www.iana.org/assignments/'):
        self.base_url = base_url

    def _get_xml(self, relative_url):
        req = urllib2.Request(
            urlparse.urljoin(self.base_url, relative_url),
            headers={'Accept': 'text/xml, application/xml',
                     'User-Agent': 'HTTPolice-IANA-tool Python-urllib'})
        return lxml.etree.parse(urllib2.urlopen(req))

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

    def get_all(self):
        tree = self._get_xml('message-headers/message-headers.xml')
        entries = []
        for record in tree.findall('//iana:record', self.xmlns):
            if record.find('iana:protocol', self.xmlns).text != 'http':
                continue
            value = record.find('iana:value', self.xmlns)
            entry = {
                '_': FieldName(value.text),
                '_citations': list(self.extract_citations(record)),
            }
            entries.append(entry)
            status = record.find('iana:status', self.xmlns)
            if (status is not None) and status.text:
                entry['iana_status'] = status.text
        return [('headers', entries, h)]


class MethodRegistry(Registry):

    def get_all(self):
        tree = self._get_xml('http-methods/http-methods.xml')
        entries = []
        for record in tree.findall('//iana:record', self.xmlns):
            entries.append({
                '_': Method(record.find('iana:value', self.xmlns).text),
                '_citations': list(self.extract_citations(record)),
                'safe': yes_no(record.find('iana:safe', self.xmlns).text),
                'idempotent':
                    yes_no(record.find('iana:idempotent', self.xmlns).text),
            })
        return [('methods', entries, m)]


class StatusCodeRegistry(Registry):

    def get_all(self):
        tree = self._get_xml('http-status-codes/http-status-codes.xml')
        entries = []
        for record in tree.findall('//iana:record', self.xmlns):
            value = record.find('iana:value', self.xmlns).text
            if not value.isdigit():
                continue
            description = record.find('iana:description', self.xmlns).text
            if description.lower() == 'unassigned':
                continue
            entries.append({
                '_': StatusCode(value),
                '_citations': list(self.extract_citations(record)),
                'description': description,
            })
        return [('status codes', entries, st)]


class ParametersRegistry(Registry):

    def get_all(self):
        tree = self._get_xml('http-parameters/http-parameters.xml')
        return [
            ('transfer codings', list(self._transfer_codings(tree)), tc),
        ]

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

    def get_all(self):
        tree = self._get_xml('media-types/media-types.xml')
        entries = []
        for record in tree.findall('//iana:record', self.xmlns):
            toplevel = record.getparent().get('id')
            subtype = record.find('iana:name', self.xmlns).text.lower()
            if subtype.startswith('vnd.') or subtype.startswith('prs.'):
                continue
            if len(subtype.split()) > 1:
                if ('deprecated' in subtype) or ('obsoleted' in subtype):
                    entry = {'deprecated': True}
                    subtype = subtype.split()[0]
                else:
                    continue
            else:
                entry = {}
            entry['_'] = MediaType(u'%s/%s' % (toplevel, subtype))
            entry['_citations'] = list(self.extract_citations(record))
            if not entry['_citations']:
                continue
            entries.append(entry)
        return [('media types', entries, media)]
