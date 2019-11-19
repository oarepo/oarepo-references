# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records"""

from __future__ import absolute_import, print_function
from invenio_records.signals import after_record_insert, after_record_update, after_record_delete, before_record_update

from oarepo_references.api import RecordReferenceAPI
from oarepo_references.signals import create_references_record, update_references_record, delete_references_record, \
    convert_record_refs

from . import config


class _RecordReferencesState(object):
    """State for record references."""

    def __init__(self, app):
        """Initialize state."""
        self.app = app
        self.api = RecordReferenceAPI()

    def get_records(self, reference):
        return self.api.get_records(reference)

    def reindex_referencing_records(self, ref=None, record=None):
        self.api.reindex_referencing_records(ref, record)

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
        self.init_config(app)

        # Connect invenio-records signal handlers
        after_record_insert.connect(create_references_record)
        before_record_update.connect(convert_record_refs)
        after_record_update.connect(update_references_record)
        after_record_delete.connect(delete_references_record)

        state = _RecordReferencesState(app)
        app.extensions['oarepo-references'] = state
        return state

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith('OAREPO_REFERENCES_'):
                app.config.setdefault(k, getattr(config, k))
