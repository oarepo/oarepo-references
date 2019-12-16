# -*- coding: utf-8 -*-
"""Model unit tests."""
import pytest
from flask_taxonomies.models import MovePosition, TaxonomyError
from flask_taxonomies.proxies import current_flask_taxonomies

from oarepo_references.proxies import current_oarepo_references


@pytest.mark.usefixtures("db")
class TestOArepoReferencesAPI:
    """Taxonomy model tests."""

    def test_get_records(self, records):
        print(records)

        recs = list(current_oarepo_references.get_records('ref1'))
        assert len(recs) == 1

        assert recs[0].record_uuid == records[0].model.id

        recs = list(current_oarepo_references.get_records('ref2'))
        assert len(recs) == 1

        assert recs[0].record_uuid == records[1].model.id

        recs = list(current_oarepo_references.get_records('ref3'))
        assert len(recs) == 1

        assert recs[0].record_uuid == records[2].model.id

        recs = list(current_oarepo_references.get_records('ref4'))
        assert len(recs) == 1

        assert recs[0].record_uuid == records[2].model.id
