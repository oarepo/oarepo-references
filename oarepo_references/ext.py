# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records."""

from __future__ import absolute_import, print_function

from oarepo_references.api import RecordReferenceAPI


class _RecordReferencesState(RecordReferenceAPI):
    """State for record references."""

    def __init__(self, app):
        """Initialize state."""
        self.app = app
        super(_RecordReferencesState, self).__init__()


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
