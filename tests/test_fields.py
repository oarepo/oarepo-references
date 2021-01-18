# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test OARepo references fields."""
import uuid

import pytest
from tests.test_utils import TestSchema

from oarepo_references.mixins import ReferenceFieldMixin


@pytest.mark.usefixtures("db")
class TestOArepoReferencesFields:
    """OARepo references fields test."""

    def test_reference_field(self, test_record_data, referenced_records):
        """Test marshmallow schema ReferenceField methods."""
        schema = TestSchema()
        rf = schema.fields['ref']
        assert isinstance(rf, ReferenceFieldMixin)

        rec_uuid = referenced_records[0].id
        rf.register(test_record_data['taxo1']['links']['self'], rec_uuid, True)
        assert len(rf.context['references']) == 1
        ref = rf.context['references'][0]
        assert ref['reference'] == \
            test_record_data['taxo1']['links']['self']
        assert ref['reference_uuid'] == rec_uuid


    def test_marshmallow_load(self, test_record_data):
        """Test marshmallow schema load."""
        schema = TestSchema()
        res = schema.load(test_record_data, partial=True)

        assert res == test_record_data
