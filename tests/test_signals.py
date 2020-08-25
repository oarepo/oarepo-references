# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test signal handler functions."""
import pytest
from sqlalchemy.exc import IntegrityError

from oarepo_references.models import RecordReference, ReferencingRecord
from oarepo_references.signals import create_references_record,\
    set_references_from_context, update_references_record
from tests.test_utils import TestRecord, TaxonomyRecord


def test_set_references_from_context(referencing_records, referenced_records):
    """Test if oarepo references are set from a record validation ctx."""
    rec = referencing_records[0]
    ref = referenced_records[0]

    ctx = dict(references=[
        dict(
            reference=None,
            reference_uuid=ref.id,
            inline=False
        )
    ])

    rec = set_references_from_context(rec, rec, ctx, True)
    assert rec.oarepo_references == ctx['references']
    assert len(rec.oarepo_references) == 1
    assert rec.oarepo_references[0] == dict(
        reference=None,
        reference_uuid=ref.id,
        inline=False
    )


def test_create_references_record(db, referencing_records, test_record_data):
    """Test that a reference record is created."""
    new_rec = TestRecord(test_record_data)

    # Test calling on record without properly initialized model yet
    with pytest.raises(AttributeError):
        create_references_record(new_rec, new_rec)

    # Test create record references for new record
    new_rec.oarepo_references = [
        {
            'reference': 'http://localhost/api/taxonomies/requestors/a/b/1',
            'reference_uuid': None,
            'inline': False
        },
        {
            'reference': 'http://localhost/api/taxonomies/requestors/a/c/2',
            'reference_uuid': None,
            'inline': False
        }
    ]
    create_references_record(new_rec, new_rec)
    db.session.commit()

    rr = ReferencingRecord.query.filter(ReferencingRecord.record_uuid == new_rec.id).one()
    assert len(rr.references) == 2
    assert set([r.reference for r in rr.references]) == \
        {'http://localhost/api/taxonomies/requestors/a/b/1',
         'http://localhost/api/taxonomies/requestors/a/c/2'}

    # Test calling create on already existing record uuid fails
    with pytest.raises(IntegrityError):
        create_references_record(referencing_records[0], referencing_records[0], throw=True)


def test_update_references_record(db, referenced_records, referencing_records, test_record_data):
    """Test that we can update an existing reference record."""
    rr = TestRecord.create(test_record_data)
    tr = TaxonomyRecord.create({
        'links': {
            'self': 'http://localhost/api/taxonomies/requestors/a/c/',
        },
        'slug': 'c'
    })
    tr['title'] = 'change'
    tr.commit()

    update_references_record(tr, tr)
    updated = TestRecord.get_record(rr.id)
    assert updated.dumps().get('sub').get('taxo2').get('title') == 'change'


def test_delete_references_record(referencing_records):
    """Test that we can delete references record."""
    deleted = referencing_records[2]

    rr = ReferencingRecord.query.filter(ReferencingRecord.record_uuid == deleted.model.id).all()
    assert len(rr) == 2

    delete_references_record(deleted, deleted)
    rr = ReferencingRecord.query.filter(ReferencingRecord.record_uuid == deleted.model.id).all()
    assert len(rr) == 0
