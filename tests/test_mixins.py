# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test OARepo references fields."""
import pytest
from tests.test_utils import TestRecord


@pytest.mark.usefixtures("db")
class TestOArepoMixins:
    """OARepo references mixins."""

    def test_update_inline_ref(self, referenced_records, test_record_data):
        """Test Reference enabled record Mixin update method."""

        rec = TestRecord.create(test_record_data)
        ref = {'links': {
            'self': 'http://localhost/api/taxonomies/requestors/a/b/',
        }, 'slug': 'b', 'title': 'new title'}

        rec.update_inlined_ref('http://localhost/api/taxonomies/requestors/a/b/', None, ref)
        assert rec['taxo1']['title'] == 'new title'
