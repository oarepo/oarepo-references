# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test signal handler functions."""
import uuid

import pytest
from invenio_records import Record
from invenio_records.errors import MissingModelError
from invenio_records.models import RecordMetadata

from oarepo_references.models import RecordReference
from oarepo_references.signals import convert_record_refs, convert_to_ref, \
    create_references_record, delete_references_record, \
    update_references_record


def test_convert_to_ref():
    """Test if taxonomies are converted to refs."""
    test_cases = [
        ({
             'links': {
                 'parent': 'http://localhost/api/taxonomies/requestors/a/',
                 'parent_tree': 'http://localhost/api/taxonomies/requestors/a/?drilldown=True',
                 'self': 'http://localhost/api/taxonomies/requestors/a/b/',
                 'tree': 'http://localhost/api/taxonomies/requestors/a/b/?drilldown=True'
             },
             'slug': 'b'
         }, {
             '$ref': 'http://localhost/api/taxonomies/requestors/a/b/',
         })
    ]
    for case in test_cases:
        in_data, expected = case
        res = convert_to_ref(in_data)
        assert res == expected


def test_convert_record_refs(test_record_data):
    """Test if any taxonomy references in record are converted to refs."""
    test_cases = [
        (test_record_data,
         {
             'pid': 999,
             'title': 'rec1',
             'taxo1': {
                 '$ref': 'http://localhost/api/taxonomies/requestors/a/b/',
             },
             'sub': {
                 'taxo2': {
                     '$ref': 'http://localhost/api/taxonomies/requestors/a/c/',
                 }
             }
         }),
    ]
    for case in test_cases:
        record, expected = case
        res = convert_record_refs(None, record)
        assert res == expected


def test_create_references_record(db, referencing_records, test_record_data):
    """Test that a reference record is created."""
    rd = convert_record_refs(None, test_record_data)
    new_rec = Record(rd)

    # Test calling on record without properly initialized model yet
    with pytest.raises(MissingModelError):
        create_references_record(new_rec, new_rec)

    id = uuid.uuid4()
    new_rec.model = RecordMetadata(id=id, json=rd)

    # Test create record references for new record
    create_references_record(new_rec, new_rec)
    db.session.commit()

    rr = RecordReference.query.filter(RecordReference.record_uuid == id).all()
    assert len(rr) == 2
    assert set([r.reference for r in rr]) == \
        {'http://localhost/api/taxonomies/requestors/a/b/',
         'http://localhost/api/taxonomies/requestors/a/c/'}

    # Test calling create on already existing record uuid fails
    with pytest.raises(FileExistsError):
        create_references_record(referencing_records[0], referencing_records[0], throw=True)


def test_update_references_record(db, referencing_records, test_record_data):
    """Test that we can update an existing reference record."""
    rec = referencing_records[0]
    rec['$ref'] = 'http://localhost/records/3'
    rec['title'] = 'changed'
    with pytest.raises(AttributeError):
        update_references_record(rec, rec)

    rec.canonical_url = 'http://localhost/records/c'

    update_references_record(rec, rec)
    rr = RecordReference.query.filter(RecordReference.record_uuid == rec.model.id).all()
    assert rr[0].reference == 'http://localhost/records/3'


def test_delete_references_record(referencing_records):
    """Test that we can delete references record."""
    deleted = referencing_records[2]

    rr = RecordReference.query.filter(RecordReference.record_uuid == deleted.model.id).all()
    assert len(rr) == 2

    delete_references_record(deleted, deleted)
    rr = RecordReference.query.filter(RecordReference.record_uuid == deleted.model.id).all()
    assert len(rr) == 0
