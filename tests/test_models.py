# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test references models."""
import uuid

import pytest
from invenio_records import Record
from sqlalchemy.exc import IntegrityError
from tests.conftest import get_ref_url
from tests.test_utils import TestRecord

from oarepo_references.models import ClassName, RecordReference, \
    ReferencingRecord
from oarepo_references.utils import class_import_string


@pytest.mark.usefixtures("db")
class TestReferencesModels:
    """OARepo references model tests."""

    def test_class_name_create(self, db, referencing_records):
        """Test create ClassName."""
        rec = referencing_records[0]

        cn = ClassName.create(name=str(class_import_string(Record)))
        db.session.commit()

        retrieved = ClassName.query.get(cn.id)
        assert retrieved.name == str(class_import_string(Record))

        with pytest.raises(IntegrityError):
            cn = ClassName.create(name=str(class_import_string(rec)))
            db.session.commit()

    def test_referencing_record_create(self, db, referencing_records, class_names):
        """Test create ReferencingRecord."""
        id = uuid.uuid4()
        rr = ReferencingRecord.create(record_uuid=id, class_name=class_names[0])
        db.session.commit()

        assert rr.record_uuid == id
        assert rr.class_name.name == class_names[0].name

    def test_reference_record_create(self, db, test_record_data, referenced_records):
        """Test create ReferenceRecord for a certain record."""
        rec = TestRecord.create(test_record_data)
        ref = referenced_records[0]
        reference = get_ref_url(ref['pid'])

        rr = RecordReference.create(rec, reference, ref.id, inline=True)
        db.session.commit()

        retrieved = RecordReference.query.get(rr.id)
        assert retrieved.record.record_uuid == rec.id
        assert retrieved.record.class_name.name == str(class_import_string(rec))
        assert retrieved.reference == reference
        assert retrieved.reference_uuid == ref.id
        assert retrieved.inline is True
