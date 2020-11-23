# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test utility functions."""

import pytest
from celery import shared_task
from flask import url_for
from invenio_records import Record
from invenio_records_rest.schemas.fields import SanitizedUnicode
from marshmallow import INCLUDE, Schema
from marshmallow.fields import URL, Integer, Nested
from oarepo_validate import MarshmallowValidatedRecordMixin

from oarepo_references.mixins import InlineReferenceMixin, \
    ReferenceByLinkFieldMixin, ReferenceEnabledRecordMixin
from oarepo_references.utils import get_reference_uuid, run_task_on_referrers


class URLReferenceField(ReferenceByLinkFieldMixin, URL):
    """URL reference marshmallow field."""


class TaxonomySchema(InlineReferenceMixin, Schema):
    """Taxonomy schema."""

    class Meta:
        unknown = INCLUDE

    def ref_url(self, data):
        return data.get('links').get('self')


class NestedTaxonomySchema(Schema):
    """Nested Taxonomy schema."""
    taxo2 = Nested(TaxonomySchema, required=False)


class URLReferenceSchema(Schema):
    """Schema for an URL reference."""
    title = SanitizedUnicode()
    ref = URLReferenceField(data_key='$ref', name='$ref', attribute='$ref')


class TestSchema(Schema):
    """Test record schema."""
    title = SanitizedUnicode()
    pid = Integer()
    taxo1 = Nested(TaxonomySchema, required=False)
    sub = Nested(NestedTaxonomySchema, required=False)
    ref = URLReferenceField(data_key='$ref', name='$ref', attribute='$ref', required=False)
    reflist = Nested(URLReferenceSchema, many=True, required=False)


class TestRecord(MarshmallowValidatedRecordMixin,
                 ReferenceEnabledRecordMixin,
                 Record):
    """Reference enabled test record class."""
    MARSHMALLOW_SCHEMA = TestSchema
    VALIDATE_MARSHMALLOW = True
    VALIDATE_PATCH = True

    @property
    def canonical_url(self):
        return url_for('invenio_records_rest.recid_item',
                       pid_value=self['pid'], _external=True)


class TaxonomyRecord(MarshmallowValidatedRecordMixin,
                     ReferenceEnabledRecordMixin,
                     Record):
    """Record for testing inlined taxonomies."""
    MARSHMALLOW_SCHEMA = TaxonomySchema
    VALIDATE_MARSHMALLOW = True
    VALIDATE_PATCH = True

    @property
    def canonical_url(self):
        return url_for('invenio_records_rest.recid_item',
                       pid_value=self['pid'], _external=True)


@pytest.mark.celery()
def test_run_task_on_referrers(referencing_records,
                               referenced_records,
                               celery_app,
                               celery_includes):
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
        nonlocal tasklist
        tasklist.append(kwargs['record'])

    @shared_task
    def _test_failing_task(*args, **kwargs):
        raise TabError

    ret = run_task_on_referrers(referred, _test_task.s(), _test_success_task.s(), None)
    ret.get()
    print(ret.status, ret)
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


def test_get_reference_uuid(referencing_records, referenced_records):
    """Test that methods returns a valid UUID for a given reference URL."""

    # Test valid reference URL
    referrer = referencing_records[0]
    reference = get_reference_uuid(referrer['$ref'])
    assert reference == referenced_records[0].id

    # Test 404 reference URL returns None
    reference = get_reference_uuid('http://localhost/api/records/10')
    assert reference is None

    # Test invalid url returns None
    reference = get_reference_uuid('http://otherhost/api/records/1')
    assert reference is None
    reference = get_reference_uuid('hhtp//localhost/api/records/1')
    assert reference is None
