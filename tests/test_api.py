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
        records = list(current_oarepo_references.get_records())
        assert len(records) == 3
