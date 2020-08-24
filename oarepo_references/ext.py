# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records."""

from __future__ import absolute_import, print_function

from oarepo_references.api import RecordReferenceAPI


class _RecordReferencesState(object):
    """State for record references."""

    def __init__(self, app):
        """Initialize state."""
        self.app = app
        self.api = RecordReferenceAPI()

    def get_records(self, reference):
        return self.api.get_records(reference)

    def reindex_referencing_records(self, ref, ref_obj=None):
        self.api.reindex_referencing_records(ref, ref_obj)

    def update_references_from_record(self, record):
        self.api.update_references_from_record(record)


class OARepoReferences(object):
    """oarepo-references extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        state = _RecordReferencesState(app)
        app.extensions['oarepo-references'] = state
        return state
