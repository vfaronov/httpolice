# -*- coding: utf-8; -*-

"""Load, query, and update tabular data for various protocol elements.

In this module, the term "key" means the actual name or number in question,
such as ``FieldName(u'Last-Modified')`` or ``StatusCode(204)``, whereas "name"
means a Python identifier suitable for attribute access, such as
``last_modified`` or ``no_content``.

"""

import csv
from enum import Enum
import importlib
import io
import os
import pkgutil

import six

from httpolice import structure
from httpolice.citation import Citation, RFC


class Knowledge(object):

    """Manages the data for one class from :mod:`httpolice.structure`."""

    # Load "raw" data from the CSV file. Lazily "process" it on the fly.
    # Allow "unprocessing" back into "raw" and dumping, for ``tools/iana.py``.

    def __init__(self, cls, name):
        self.cls = cls
        self.name = name
        self.filename = '%s.csv' % self.name
        self.keys_by_name = {}
        self.raw_by_key = {}
        self.processed_by_key = {}

        data = pkgutil.get_data(__name__, self.filename)
        buf = io.StringIO(data.decode('ascii'), newline=u'')
        reader = csv.DictReader(buf, lineterminator=u'\n')
        self.fieldnames = reader.fieldnames
        for raw in reader:
            key = self.cls(raw['key'])
            assert key not in self.raw_by_key
            self.raw_by_key[key] = raw
            name = self.name_from_raw(key, raw)
            assert name not in self.keys_by_name
            self.keys_by_name[name] = key

        self.accessor = KnowledgeAccessor(self)

    def __contains__(self, key):
        return key in self.raw_by_key

    def __iter__(self):
        return iter(self.raw_by_key)

    def get(self, key):
        processed = self.processed_by_key.get(key)
        if processed is None:
            raw = self.raw_by_key.get(key)
            if raw is None:
                processed = {}
            else:
                processed = self.process(raw)
            self.processed_by_key[key] = processed
        return processed

    @classmethod
    def name_from_raw(cls, key, raw):
        name = key if isinstance(key, six.text_type) else raw['title']
        name = (name.
                replace(u'-', u' ').replace(u' ', u'_').replace(u'/', u'_').
                replace(u'+', u'_').replace(u'.', u'_').
                lower())
        # Python keywords can't be used as identifiers.
        if name in [u'continue', u'for', u'from', u'return']:
            name = name + u'_'
        return str(name)            # Identifier is a native string.

    def process(self, raw):
        processed = {}

        for (field, value) in raw.items():
            if not value:
                continue
            elif field == 'key':
                processed[field] = self.cls(value)
            elif value.isdigit():
                processed[field] = int(value)
            elif value.lower() in [u'true', u'false']:
                processed[field] = (value.lower() == u'true')
            elif isinstance(getattr(self, field, None), type):     # Enum
                processed[field] = getattr(self, field)[value]
            else:
                processed[field] = value

        if 'rfc' in processed:
            processed['citation'] = RFC(processed.pop('rfc'),
                                        processed.pop('rfc_section', None),
                                        processed.pop('rfc_appendix', None))
        if 'cite_url' in processed:
            processed['citation'] = Citation(processed.pop('cite_title', None),
                                             processed.pop('cite_url'))

        return processed

    def unprocess(self, processed, orig_raw):                # pragma: no cover
        # pylint: disable=unused-argument
        processed = processed.copy()

        cite = processed.pop('citation', None)
        if isinstance(cite, RFC):
            processed['rfc'] = cite.num
            processed['rfc_section'] = cite.section
            processed['rfc_appendix'] = cite.appendix
        elif isinstance(cite, Citation):
            processed['cite_url'] = cite.url
            processed['cite_title'] = cite.title

        raw = {}
        for (field, value) in processed.items():
            if hasattr(value, 'name'):                      # Enum
                raw[field] = value.name
            elif value is not None:
                raw[field] = six.text_type(value)
        return raw

    def dump(self, new):                                    # pragma: no cover
        with io.open(os.path.join(os.path.dirname(__file__), self.filename),
                     'w', newline=u'') as f:
            writer = csv.DictWriter(f, self.fieldnames, lineterminator=u'\n')
            writer.writeheader()
            for processed in new:
                orig_raw = self.raw_by_key.get(processed['key'], {})
                writer.writerow(self.unprocess(processed, orig_raw))


class KnowledgeAccessor(object):

    """
    For example, ``h.accept`` returns ``FieldName(u'Accept')``.

    This makes code visually nicer and prevents typos.
    """

    def __init__(self, knowledge):
        self.knowledge = knowledge

    def __getattr__(self, name):
        try:
            return self.knowledge.keys_by_name[name]
        except KeyError:
            raise AttributeError(name)


class SyntaxKnowledge(Knowledge):

    """Knowledge that includes a reference to a grammar symbol."""

    def process(self, raw):
        processed = super(SyntaxKnowledge, self).process(raw)
        if 'syntax_module' in processed:
            module = importlib.import_module('httpolice.syntax.%s' %
                                             processed.pop('syntax_module'))
            processed['syntax'] = getattr(module,
                                          processed.pop('syntax_symbol'))
        return processed

    def unprocess(self, processed, orig_raw):               # pragma: no cover
        # There is no reliable way to convert a reference to a `Symbol`
        # back into module name + variable name, nor do we need that,
        # so just preserve whatever we had originally.
        processed = processed.copy()
        processed.pop('syntax', None)
        processed['syntax_module'] = orig_raw.get('syntax_module', '')
        processed['syntax_symbol'] = orig_raw.get('syntax_symbol', '')
        return super(SyntaxKnowledge, self).unprocess(processed, orig_raw)

    def syntax_for(self, key):
        return self.get(key).get('syntax')


class Argument(Enum):
    no = 0
    optional = 1
    required = 2

class ArgumentKnowledge(SyntaxKnowledge):

    """Knowledge about things that can have arguments with some syntax."""

    argument = Argument

    def argument_required(self, key):
        return self.get(key).get('argument') is Argument.required

    def no_argument(self, key):
        return self.get(key).get('argument') is Argument.no


class HeaderRule(Enum):
    single = 1
    multi = 2
    special = 3

class HeaderKnowledge(SyntaxKnowledge):

    rule = HeaderRule

    def is_bad_for_connection(self, key):
        return self.get(key).get('bad_for_connection')

    def is_bad_for_trailer(self, key):
        return self.get(key).get('bad_for_trailer')

    def is_for_request(self, key):
        return self.get(key).get('for_request')

    def is_for_response(self, key):
        return self.get(key).get('for_response')

    def is_precondition(self, key):
        return self.get(key).get('precondition')

    def is_proactive_conneg(self, key):
        return self.get(key).get('proactive_conneg')

    def is_representation_metadata(self, key):
        return self.get(key).get('representation_metadata')

    def rule_for(self, key):
        return self.get(key).get('rule')

    def is_deprecated(self, key):
        return self.get(key).get('iana_status') in [u'deprecated',
                                                    u'obsoleted']

header = HeaderKnowledge(structure.FieldName, 'header')
h = header.accessor


class MethodKnowledge(Knowledge):

    @classmethod
    def name_from_raw(cls, key, raw):
        return super(MethodKnowledge, cls).name_from_raw(key, raw).upper()

    def defines_body(self, key):
        return self.get(key).get('defines_body')

    def is_cacheable(self, key):
        return self.get(key).get('cacheable')

    def is_safe(self, key):
        return self.get(key).get('safe')

method = MethodKnowledge(structure.Method, 'method')
m = method.accessor


class Cacheable(Enum):
    not_at_all = 0
    not_by_default = 1
    by_default = 2

class StatusCodeKnowledge(Knowledge):

    cacheable = Cacheable

    def is_cacheable(self, key):
        return self.get(key).get('cacheable')

status_code = StatusCodeKnowledge(structure.StatusCode, 'status_code')
st = status_code.accessor


class ArgumentForm(Enum):
    token = 1
    quoted_string = 2

class CacheDirectiveKnowledge(ArgumentKnowledge):

    argument_form = ArgumentForm

    def token_preferred(self, key):
        return self.get(key).get('argument_form') is ArgumentForm.token

    def quoted_string_preferred(self, key):
        return self.get(key).get('argument_form') is ArgumentForm.quoted_string

    def is_for_request(self, key):
        return self.get(key).get('for_request')

    def is_for_response(self, key):
        return self.get(key).get('for_response')

cache_directive = CacheDirectiveKnowledge(structure.CacheDirective,
                                          'cache_directive')
cache = cache_directive.accessor


forwarded_param = ArgumentKnowledge(structure.ForwardedParam,
                                    'forwarded_param')
forwarded = forwarded_param.accessor


class MediaTypeKnowledge(Knowledge):

    def is_deprecated(self, key):
        return self.get(key).get('deprecated')

    def is_json(self, key):
        return self.get(key).get('is_json') or key.endswith(u'+json')

    def is_xml(self, key):
        return self.get(key).get('is_xml') or key.endswith(u'+xml')

    def is_multipart(self, key):
        return key.startswith(u'multipart/')

    def is_patch(self, key):
        return self.get(key).get('patch')

media_type = MediaTypeKnowledge(structure.MediaType, 'media_type')
media = media_type.accessor


class ProductKnowledge(Knowledge):

    def is_library(self, key):
        return self.get(key).get('library')

product = ProductKnowledge(structure.ProductName, 'product')


alt_svc_param = ArgumentKnowledge(structure.AltSvcParam, 'alt_svc_param')
altsvc = alt_svc_param.accessor


auth_scheme = Knowledge(structure.AuthScheme, 'auth_scheme')
auth = auth_scheme.accessor


content_coding = Knowledge(structure.ContentCoding, 'content_coding')
cc = content_coding.accessor


hsts_directive = ArgumentKnowledge(structure.HSTSDirective, 'hsts_directive')
hsts = hsts_directive.accessor


preference = ArgumentKnowledge(structure.Preference, 'preference')
prefer = preference.accessor


range_unit = Knowledge(structure.RangeUnit, 'range_unit')
unit = range_unit.accessor


relation_type = Knowledge(structure.RelationType, 'relation_type')
rel = relation_type.accessor


transfer_coding = Knowledge(structure.TransferCoding, 'transfer_coding')
tc = transfer_coding.accessor


upgrade_token = Knowledge(structure.UpgradeToken, 'upgrade_token')
upgrade = upgrade_token.accessor


warn_code = Knowledge(structure.WarnCode, 'warn_code')
warn = warn_code.accessor


def _collect():
    globals_ = globals()
    return {globals_[name].knowledge.cls: (globals_[name].knowledge, name)
            for name in globals_
            if isinstance(globals_[name], KnowledgeAccessor)}

classes = _collect()    # dict containing items like: ``Method: (method, 'm')``


def get(obj):
    for cls, (knowledge, _) in classes.items():
        if isinstance(obj, cls):
            return knowledge.get(obj)


def citation(obj):
    return get(obj).get('citation')


def title(obj, with_citation=False):
    info = get(obj)
    t = info.get('title')
    if with_citation:
        cite = info.get('citation')
        if cite and cite.title:
            if t:
                t = u'%s (%s)' % (t, cite.title)
            else:
                t = cite.title
    return t
