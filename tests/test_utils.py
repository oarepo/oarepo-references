# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test utility functions."""
import pytest
from celery import shared_task

from oarepo_references.utils import get_reference_uuid, keys_in_dict,\
    transform_dicts_in_data, run_task_on_referrers


@pytest.mark.celery(result_backend='redis://')
def test_run_task_on_referrers(referencing_records, referenced_records):
    """Test that tasks are launched on referring records."""
    referred = 'http://localhost/records/1'
    tasklist = []

    @shared_task
    def _test_task(referrer):
        tasklist.append(referrer)

    run_task_on_referrers(referred, _test_task)
    assert len(tasklist) == 3
    assert tasklist == [
        referencing_records[0],
        referencing_records[2],
        referencing_records[3]]


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
