# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test API class methods."""
import pytest

from oarepo_references.proxies import current_oarepo_references
from oarepo_references.signals import after_reference_update


@pytest.mark.usefixtures("db")
class TestOArepoReferencesAPI:
    """Taxonomy model tests."""

    def test_get_records(self, referencing_records):
        recs = list(current_oarepo_references.get_records('http://localhost/records/1'))
        assert len(recs) == 3
        assert recs[0].record_uuid == referencing_records[0].model.id

        recs = list(current_oarepo_references.get_records('http://localhost/records/2'))
        assert len(recs) == 2
        assert recs[0].record_uuid == referencing_records[1].model.id

        recs = list(current_oarepo_references.get_records('http://localhost/records/3'))
        assert len(recs) == 0

    def test_reindex_referencing_records(self, referencing_records):
        pass
        # def _test_handler(record):
        #     def _handler(_, references, ref_obj):
        #         assert references == [record.model.id]
        #         assert ref_obj is record
        #
        #     return _handler
        #
        # handle = _test_handler(records[0])
        # after_reference_update.connect(handle)
        #
        # current_oarepo_references.reindex_referencing_records('ref1', records[0])
