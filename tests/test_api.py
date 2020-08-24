# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test API class methods."""
import pytest

from oarepo_references.signals import after_reference_update
from tests.conftest import get_ref_url
from tests.test_utils import TestRecord


@pytest.mark.usefixtures("db")
class TestOArepoReferencesAPI:
    """Taxonomy API tests."""

    def test_reference_content_changed(self, referenced_records, referencing_records,
                                       test_record_data, references_api):
        """Test reference content change handler."""
        rec = TestRecord.create(test_record_data)
        rec.commit()

        ref = referenced_records[0]
        ref['title'] = 'change'
        ref.commit()

        with pytest.raises(AssertionError):
            references_api.reference_content_changed(ref)

        updated = references_api.reference_content_changed(
            ref,
            ref_url='http://localhost/records/1',
            ref_uuid=ref.id
        )
        assert len(updated) == 3

    def test_reference_changed(self, db, referencing_records,
                               referenced_records, references_api):
        """Test reference name change handler."""
        ref = referenced_records[1]
        updated = references_api.reference_changed(
            old='http://localhost/records/2',
            new='http://localhost/records/new',
        )
        assert len(updated) == 2
        assert updated[0].dumps().get('$ref') == 'http://localhost/records/new'
        assert updated[1].dumps().get('reflist')[0].get('$ref') == 'http://localhost/records/new'

    def test_get_records(self, db, referencing_records, references_api):
        """Test that we can get reference records referencing a reference."""
        recs = list(references_api.get_records('http://localhost/records/1'))
        assert len(recs) == 3
        assert set(rc.record.record_uuid for rc in recs) == \
            set([rr.model.id for i, rr in enumerate(referencing_records) if i in [0, 2, 3]])

        recs = list(references_api.get_records('http://localhost/records/2'))
        assert len(recs) == 2
        assert set(rc.record.record_uuid for rc in recs) == \
            set([rr.model.id for i, rr in enumerate(referencing_records) if i in [1, 2]])

        recs = list(references_api.get_records('http://localhost/records/3'))
        assert len(recs) == 0

        recs = list(references_api.get_records('http://localhost/records/'))
        assert len(recs) == 5

        recs = list(references_api.get_records('http://localhost/records/', exact=True))
        assert len(recs) == 0

    def test_reindex_referencing_records(self,
                                         db,
                                         referenced_records,
                                         referencing_records,
                                         references_api):
        def _test_handler(referrers):
            def _handler(_, references, ref_obj):
                assert set(references) == set(referrers)

            return _handler

        referencing_records.pop(1)

        handle = _test_handler([r.model.id for r in referencing_records])
        after_reference_update.connect(handle)

        references_api.reindex_referencing_records(get_ref_url(referenced_records[0]['pid']))
