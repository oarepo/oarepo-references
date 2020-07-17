# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test API class methods."""
import pytest

from oarepo_references.api import RecordReferenceAPI
from oarepo_references.proxies import current_oarepo_references
from oarepo_references.signals import after_reference_update


@pytest.mark.usefixtures("db")
class TestOArepoReferencesAPI:
    """Taxonomy model tests."""

    def test_get_records(self, referencing_records, references_api):
        """Test that we can get reference records referencing a reference."""
        recs = list(references_api.get_records('http://localhost/records/1'))
        assert len(recs) == 3
        assert recs[0].record_uuid == referencing_records[0].model.id

        recs = list(references_api.get_records('http://localhost/records/2'))
        assert len(recs) == 2
        assert recs[0].record_uuid == referencing_records[1].model.id

        recs = list(references_api.get_records('http://localhost/records/3'))
        assert len(recs) == 0

        recs = list(references_api.get_records('http://localhost/records/'))
        assert len(recs) == 5

        recs = list(references_api.get_records('http://localhost/records/', exact=True))
        assert len(recs) == 0

    def test_reindex_referencing_records(self,
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

        references_api.reindex_referencing_records('http://localhost/records/1')
