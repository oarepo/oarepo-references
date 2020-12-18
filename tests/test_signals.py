# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test signal handler functions."""
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from tests.conftest import get_pid
from tests.test_utils import TaxonomyRecord, TestRecord

from oarepo_references.models import RecordReference, ReferencingRecord
from oarepo_references.proxies import current_references
from oarepo_references.signals import create_references_record, \
    delete_references_record, set_references_from_context


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
    assert set([r.reference for r in rr.references]) == {
        'http://localhost/api/taxonomies/requestors/a/b/1',
        'http://localhost/api/taxonomies/requestors/a/c/2'
    }

    # Test calling create on already existing record should not fail and do noop
    create_references_record(referencing_records[0], referencing_records[0], throw=True)
    db.session.commit()

    rr = ReferencingRecord.query.filter(ReferencingRecord.record_uuid == new_rec.id).one()
    assert len(rr.references) == 2
    assert set([r.reference for r in rr.references]) == {
        'http://localhost/api/taxonomies/requestors/a/b/1',
        'http://localhost/api/taxonomies/requestors/a/c/2'
    }


def test_update_references_record(db, test_record_data):
    """Test that we can update an existing reference record."""
    rr = TestRecord.create(test_record_data)
    rr.commit()
    content = {
        'links': {
            'self': 'http://localhost/api/taxonomies/requestors/a/c/',
        },
        'pid': get_pid()[1],
        'slug': 'c'
    }
    tr = TaxonomyRecord.create(content)
    tr.commit()

    content['title'] = 'change'
    content.pop('pid')

    current_references.reference_content_changed(
        content,
        'http://localhost/api/taxonomies/requestors/a/c/')

    updated = TestRecord.get_record(rr.id)
    assert updated.dumps().get('sub').get('taxo2').get('title') == 'change'

    taxoupdated = TaxonomyRecord.get_record(tr.id)
    assert taxoupdated.dumps().get('title') == 'change'


def test_delete_references_record(referencing_records):
    """Test that we can delete references record."""
    deleted = referencing_records[2]

    rr = ReferencingRecord.query.filter(ReferencingRecord.record_uuid == deleted.model.id).one()
    refs = RecordReference.query.filter(RecordReference.record_id == rr.id).all()
    assert rr is not None
    assert len(refs) == 2

    delete_references_record(deleted, deleted)
    with pytest.raises(NoResultFound):
        ReferencingRecord.query.filter(ReferencingRecord.record_uuid == deleted.model.id).one()

    refs = RecordReference.query.filter(RecordReference.record_id == rr.id).all()
    assert len(refs) == 0
