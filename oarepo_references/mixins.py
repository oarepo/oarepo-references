# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records."""
from invenio_records import Record
from oarepo_validate import before_marshmallow_validate, after_marshmallow_validate


class ReferenceEnabledRecordMixin(object):
    """Record that contains inlined references to other records."""

    def update_inlined_ref(self, url, uuid, ref_obj):
        """Update inlined reference content in a record."""
        self.commit(**ref_obj)
