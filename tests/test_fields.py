# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test OARepo references fields."""
import pytest
from tests.test_utils import TestSchema

from oarepo_references.mixins import ReferenceFieldMixin


@pytest.mark.usefixtures("db")
class TestOArepoReferencesFields:
    """OARepo references fields test."""

    def test_reference_field(self, test_record_data):
        """Test marshmallow schema ReferenceField methods."""
        schema = TestSchema()
        rf = schema.fields['ref']
        assert isinstance(rf, ReferenceFieldMixin)

        rf.register(test_record_data['taxo1']['links']['self'], None, True)
        assert len(rf.context['references']) == 1
        assert rf.context['references'][0]['reference'] == \
            test_record_data['taxo1']['links']['self']

    def test_marshmallow_load(self, test_record_data):
        """Test marshmallow schema load."""
        schema = TestSchema()
        res = schema.load(test_record_data, partial=True)

        assert res == test_record_data
