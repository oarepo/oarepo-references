# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test utility functions."""
import typing

import pytest
from celery import shared_task
from invenio_records import Record
from invenio_records_rest.schemas.fields import SanitizedUnicode
from marshmallow import Schema, missing, post_load
from marshmallow.fields import URL, Field, Nested, Integer
from oarepo_validate import MarshmallowValidatedRecordMixin

from oarepo_references.mixins import ReferenceEnabledRecordMixin
from oarepo_references.schemas.fields.reference import ReferenceFieldMixin
from oarepo_references.utils import get_reference_uuid, keys_in_dict, \
    run_task_on_referrers, transform_dicts_in_data


class URLReferenceField(ReferenceFieldMixin, URL):
    """URL reference marshmallow field."""

    def deserialize(self,
                    value: typing.Any,
                    attr: str = None,
                    data: typing.Mapping[str, typing.Any] = None,
                    **kwargs):
        output = super(URLReferenceField, self).deserialize(value, attr, data, **kwargs)
        if output is missing:
            return output

        changes = self.context.get('changed_reference', None)
        self.register(output, None, False)
        return output


class LinksField(Field):
    """Taxonomy links field."""
    self = URLReferenceField()


class TaxonomySchema(Schema):
    """Taxonomy schema."""
    links = LinksField()
    slug = SanitizedUnicode()

    @post_load
    def update_inline_changes(self, data, many, **kwargs):
        changes = self.context.get('changed_reference', None)
        if changes and changes['url'] == self.self_url(data):
            data = changes['content']
        return data

    def self_url(self, data):
        return data.get('links').get('self')

class NestedTaxonomySchema(Schema):
    """Nested Taxonomy schema."""
    taxo2 = Nested(TaxonomySchema(), required=False)


class URLReferenceSchema(Schema):
    """Schema for an URL reference."""
    title = SanitizedUnicode()
    ref = URLReferenceField(data_key='$ref', name='$ref', attribute='$ref')


class TestSchema(Schema):
    """Test record schema."""
    title = SanitizedUnicode()
    pid = Integer()
    taxo1 = Nested(TaxonomySchema(), required=False)
    sub = Nested(NestedTaxonomySchema(), required=False)
    ref = URLReferenceField(data_key='$ref', name='$ref', attribute='$ref', required=False)
    reflist = Nested(URLReferenceSchema, many=True, required=False)


class TestRecord(MarshmallowValidatedRecordMixin,
                 ReferenceEnabledRecordMixin,
                 Record):
    """Reference enabled test record class."""
    MARSHMALLOW_SCHEMA = TestSchema
    VALIDATE_MARSHMALLOW = True
    VALIDATE_PATCH = True


@pytest.mark.celery(result_backend='redis://')
def test_run_task_on_referrers(referencing_records, referenced_records):
    """Test that tasks are launched on referring records."""
    referred = 'http://localhost/records/1'
    referers = [
        referencing_records[0],
        referencing_records[2],
        referencing_records[3]]
    tasklist = []
    success = False

    @shared_task
    def _test_success_task(*args, **kwargs):
        assert kwargs['records'] == referers
        nonlocal success
        success = True

    @shared_task
    def _test_error_task(*args, **kwargs):
        assert kwargs['record'] == referencing_records[0]
        nonlocal success
        success = False

    @shared_task
    def _test_task(*args, **kwargs):
        tasklist.append(kwargs['record'])

    @shared_task
    def _test_failing_task(*args, **kwargs):
        raise TabError

    run_task_on_referrers(referred, _test_task.s(), _test_success_task.s(), None)
    assert len(tasklist) == 3
    assert tasklist == referers
    assert success is True

    try:
        run_task_on_referrers(referred,
                              _test_failing_task.s(),
                              _test_success_task.s(),
                              _test_error_task.s())
    except TabError:
        pass
    assert success is False


def test_transform_dicts_in_data():
    """Test transformation of dicts in data."""
    test_cases = [
        ({'a': 'c'}, lambda x: {**x, 'b': 'd'}, {'a': 'c', 'b': 'd'}),
        ([{'a': 'c'}, {'d': 'e'}],
         lambda x: {**x, 'b': 'd'},
         {'_': [{'a': 'c', 'b': 'd'}, {'b': 'd', 'd': 'e'}]}),
        ([{'a': 'c'}, {'d': 'e'}, [{'x': 'y'}]],
         lambda x: {**x, 'b': 'd'},
         {'_': [{'a': 'c', 'b': 'd'},
                {'b': 'd', 'd': 'e'},
                [{'b': 'd', 'x': 'y'}]]})
    ]

    for case in test_cases:
        data, transform, expected = case
        res = transform_dicts_in_data(data, transform)
        assert res == expected


def test_keys_in_dict():
    """Test that we could find a key anywhere in a given data."""
    test_cases = [
        ({'$ref': 'a'}, None, ['a']),
        ({'c': {'$ref': 'a'}}, None, ['a']),
        ({'c': {'$ref': 'a'}, 'b': {'$ref': 'c'}}, None, ['a', 'c']),
        ({'c': {'$ref': 'a'}, 'b': [{'f': 'g'}, {'d': 'e', '$ref': 'c'}]}, None, ['a', 'c']),
        ([{'$ref': 'g'}, {'c': {'$ref': 'a'}}], None, ['g', 'a']),
        ([{'$ref': 3}, {'c': {'$ref': 'a'}}], int, [3]),
    ]

    for case in test_cases:
        data, required, expected = case
        res = list(keys_in_dict(data, required_type=required))
        assert res == expected


def test_get_reference_uuid(referencing_records, referenced_records):
    """Test that methods returns a valid UUID for a given reference URL."""

    # Test valid reference URL
    referrer = referencing_records[0]
    reference = get_reference_uuid(referrer['$ref'])
    assert reference == referenced_records[0].id

    # Test 404 reference URL returns None
    reference = get_reference_uuid('http://localhost/records/10')
    assert reference is None

    # Test invalid url returns None
    reference = get_reference_uuid('http://otherhost/records/1')
    assert reference is None
    reference = get_reference_uuid('hhtp//localhost/records/1')
    assert reference is None
