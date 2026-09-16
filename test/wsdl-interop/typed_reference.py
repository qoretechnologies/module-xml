"""Checked PSVI observations and independent native-value/character comparisons.

Copyright (C) 2026 Qore Technologies, s.r.o.
This is an oracle-harness predicate, not a replacement for source adjudication.
Element-only siblings use an explicit exact/per-name ordering contract. Mixed
and generic characters and child order are always retained. Complete XML carrier
checks separately own comments, processing instructions and lexical boundaries.
"""
import base64
import re
from lxml import etree

import calendar_reference
import temporal_reference
import duration_reference

XML = 'http://www.w3.org/XML/1998/namespace'
CALENDARS = {7: 'duration', 8: 'dateTime', 9: 'time', 10: 'date', 11: 'gYearMonth',
             12: 'gYear', 13: 'gMonthDay', 14: 'gDay', 15: 'gMonth'}
PSVI_KEYS = {'attempted', 'validity', 'type', 'member', 'value', 'value_type',
             'schema_specified', 'list_members', 'list_types'}
MAX_DEPTH = 256


def _ncname(value):
    if not isinstance(value, str) or not value or ':' in value or value.startswith('{'):
        return False
    try:
        return etree.QName(value).namespace is None
    except ValueError:
        return False


def _name(value, *, anonymous=False):
    if not isinstance(value, str):
        return False
    if anonymous and re.fullmatch(r'anonymous:(0|[1-9][0-9]*)', value):
        return True
    return value.startswith('{') and '}' in value and _ncname(value.rsplit('}', 1)[1])


def _actual(value, primitive):
    if primitive in (0, 45):
        if value is not None:
            raise ValueError('unavailable primitive has an actual value')
        return
    if primitive == 3:
        if type(value) is not bool:
            raise ValueError('boolean primitive requires a boolean value')
        return
    if primitive in (1, 2, 18, *range(21, 30)):
        if not isinstance(value, str):
            raise ValueError('string primitive requires a string value')
        return
    expected = ('decimal' if primitive == 4 or primitive in range(30, 43) else
                'float' if primitive == 5 else 'double' if primitive == 6 else
                'calendar' if primitive in CALENDARS else 'binary' if primitive in (16, 17) else
                'QName' if primitive in (19, 20) else None)
    if not isinstance(value, dict) or value.get('kind') != expected or expected is None:
        raise ValueError('actual value does not match its primitive kind')
    field = {'QName': 'expanded', 'decimal': 'value', 'float': 'bits', 'double': 'bits',
             'binary': 'base64', 'calendar': 'lexical'}[expected]
    if set(value) != {'kind', field} or not isinstance(value[field], str):
        raise ValueError('unknown or malformed typed scalar fields')
    lexical = value[field]
    if expected == 'QName' and not _name(lexical):
        raise ValueError('malformed expanded QName observation')
    if expected == 'decimal' and not re.fullmatch(r'-?(0|[1-9][0-9]*)(\.[0-9]+)?', lexical):
        raise ValueError('malformed exact decimal observation')
    if expected in ('float', 'double') and (not re.fullmatch(r'0|[1-9][0-9]{0,19}', lexical)
            or int(lexical) >= (1 << (32 if expected == 'float' else 64))):
        raise ValueError('malformed IEEE bit observation')
    if expected == 'binary':
        try:
            decoded = base64.b64decode(lexical, validate=True)
        except ValueError as error:
            raise ValueError('malformed binary observation') from error
        if base64.b64encode(decoded).decode('ascii') != lexical:
            raise ValueError('noncanonical binary observation')
    if expected == 'calendar':
        _scalar(value, primitive)


def _psvi(value, *, attribute=False):
    if not isinstance(value, dict):
        raise ValueError('missing PSVI observation')
    extra = {'lexical'} if attribute else {'nil'}
    if value.get('assessment') == 'absent':
        if not attribute or set(value) != {'assessment', 'lexical'} or not isinstance(value['lexical'], str):
            raise ValueError('malformed absent attribute assessment')
        return
    expected = PSVI_KEYS | extra
    if not attribute and 'content_type' in value:
        expected |= {'content_type'}
        if type(value['content_type']) is not int or value['content_type'] not in (0, 1, 2, 3):
            raise ValueError('invalid complex content category')
    if set(value) != expected:
        raise ValueError('incomplete or unexpected PSVI fields')
    for name in ('attempted', 'validity'):
        if type(value[name]) is not int or value[name] not in ((0, 1, 2) if name == 'attempted' else (0, 2)):
            raise ValueError('invalid PSVI assessment status')
    if (value['attempted'] == 0) != (value['validity'] == 0):
        raise ValueError('inconsistent PSVI assessment status')
    if type(value['schema_specified']) is not bool or (not attribute and type(value['nil']) is not bool):
        raise ValueError('invalid nil/default assessment flag')
    if attribute and not isinstance(value['lexical'], str):
        raise ValueError('missing attribute lexical observation')
    for name in ('type', 'member'):
        if value[name] is not None and not _name(value[name], anonymous=True):
            raise ValueError('invalid assessed type identity')
    kind = value['value_type']
    if type(kind) is not int or kind not in range(46):
        raise ValueError('unknown primitive value kind')
    kinds, members = value['list_types'], value['list_members']
    if (not isinstance(kinds, list) or any(type(v) is not int or v not in range(1, 43) for v in kinds)
            or not isinstance(members, list) or any(v is not None and not _name(v, anonymous=True) for v in members)):
        raise ValueError('invalid selected list item types')
    actual = value['value']
    if kind in (43, 44):
        if (not isinstance(actual, list) or len(kinds) != (len(actual) if kind == 43 else 1)
                or len(members) != len(actual)
                or (kind == 43 and any(v is None for v in members))
                or (kind == 44 and any(v is not None for v in members))):
            raise ValueError('inconsistent selected list item cardinality')
        for index, item in enumerate(actual):
            _actual(item, kinds[index] if kind == 43 else kinds[0])
    else:
        if kinds or members:
            raise ValueError('non-list value has list item metadata')
        _actual(actual, kind)


def validate_observation(observation):
    """Fail closed on missing/unknown fields and bounded-tree protocol corruption.

    A reference observation beyond 256 element levels fails the harness; it is
    never classified as an invalid production document or a passing comparison.
    """
    if (not isinstance(observation, dict) or set(observation) != {'format', 'root'}
            or type(observation['format']) is not int or observation['format'] != 1):
        raise ValueError('unsupported typed observation format')
    pending = [(observation['root'], 1)]
    while pending:
        node, depth = pending.pop()
        if depth > MAX_DEPTH:
            raise ValueError('typed observation exceeds depth limit')
        if (not isinstance(node, dict) or set(node) != {'name', 'attributes', 'content', 'namespace_declarations', 'psvi'}
                or not _name(node['name']) or not isinstance(node['attributes'], dict)
                or not isinstance(node['namespace_declarations'], dict) or not isinstance(node['content'], list)):
            raise ValueError('malformed typed element observation')
        namespaces = node['namespace_declarations']
        if (('xml' in namespaces and namespaces['xml'] != XML)
                or 'xmlns' in namespaces or any((prefix != '' and not _ncname(prefix)) or not isinstance(uri, str)
                       for prefix, uri in namespaces.items())):
            raise ValueError('malformed namespace context')
        _psvi(node['psvi'])
        for name, attr in node['attributes'].items():
            if not _name(name):
                raise ValueError('malformed expanded attribute name')
            _psvi(attr, attribute=True)
        for child in node['content']:
            if not isinstance(child, str):
                pending.append((child, depth + 1))


def _scalar(value, kind):
    if isinstance(value, dict) and value.get('kind') == 'calendar':
        if kind not in CALENDARS:
            raise ValueError('calendar value has a noncalendar primitive kind')
        name, lexical = CALENDARS[kind], value['lexical']
        if name == 'duration':
            return name, duration_reference.value(lexical)
        if name in ('dateTime', 'time'):
            actual = temporal_reference.value(name, lexical)
            return name, actual.zoned, actual.minute, actual.second
        actual = calendar_reference.value(name, lexical)
        return name, actual.zoned, actual.minute
    return value


def _namespace_dependencies(text, namespaces):
    """Retain the meaning of possible QName tokens in uninterpreted lexical data."""
    prefixes = set()
    for token in re.findall(r'[^ \t\r\n]+', text):
        parts = token.split(':')
        if len(parts) <= 2 and all(_ncname(part) for part in parts):
            prefixes.add(parts[0] if len(parts) == 2 else '')
    return {prefix: namespaces.get(prefix) for prefix in sorted(prefixes)}


def _value(value):
    # Schema-specified defaults and materialized equivalent attributes have the
    # same assessed value. Keep the provenance in the raw report, not equality.
    result = {key: item for key, item in value.items() if key not in ('lexical', 'schema_specified')}
    actual = result.get('value')
    if isinstance(actual, list):
        kinds = result['list_types']
        result['value'] = [_scalar(item, kinds[0] if len(kinds) == 1 else kinds[i])
                           for i, item in enumerate(actual)]
    else:
        result['value'] = _scalar(actual, result.get('value_type'))
    if result.get('attempted', 0) == 0 and 'lexical' in value:
        result['lexical'] = value['lexical']
    return result


def _element(node, order, namespaces):
    # Store only local declarations in the observation. An undo log preserves
    # ancestor/sibling scopes without quadratic copies on namespace-deep trees.
    missing = object()
    previous = {prefix: namespaces.get(prefix, missing) for prefix in node['namespace_declarations']}
    namespaces.update(node['namespace_declarations'])
    try:
        value = _value(node['psvi'])
        mixed = value.get('content_type') == 3 or value.get('attempted') == 0
        content, attributes = [], {}
        bindings = {'attributes': {}, 'text': [], 'simple': {}}
        for name, attr in node['attributes'].items():
            attributes[name] = _value(attr)
            if attr.get('attempted', 0) == 0 or attr.get('value_type') == 1:
                bindings['attributes'][name] = _namespace_dependencies(attr['lexical'], namespaces)
        for item in node['content']:
            if isinstance(item, dict):
                content.append(_element(item, order, namespaces))
            elif mixed:
                content.append(item)
                bindings['text'].append(_namespace_dependencies(item, namespaces))
        if value.get('value_type') == 1 and isinstance(value.get('value'), str):
            bindings['simple'] = _namespace_dependencies(value['value'], namespaces)
        if order == 'per-name' and value.get('content_type') == 2:
            content.sort(key=lambda child: child['name'])
        return {'name': node['name'], 'attributes': attributes, 'value': value,
                'content': content, 'lexical_bindings': bindings}
    finally:
        for prefix, prior in previous.items():
            if prior is missing:
                del namespaces[prefix]
            else:
                namespaces[prefix] = prior


def compare(before, after, *, order):
    """Compare checked observations with an explicit element-only order contract.

    Prefix spelling is irrelevant for assessed QName values and expanded names.
    Uninterpreted QName-like lexical tokens retain their actual namespace binding,
    including absence. Generic/mixed text always retains exact character order.
    Unknown fields/kinds or incomplete observations raise; they never pass.
    """
    if order not in ('exact', 'per-name'):
        raise ValueError('unknown typed comparison ordering contract')
    validate_observation(before)
    validate_observation(after)
    return (_element(before['root'], order, {'': '', 'xml': XML})
            == _element(after['root'], order, {'': '', 'xml': XML}))
