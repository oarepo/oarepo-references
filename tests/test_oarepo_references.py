# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask
from invenio_records.signals import after_record_insert
from oarepo_validate import after_marshmallow_validate

from oarepo_references import OARepoReferences
from oarepo_references.signals import create_references_record, \
    set_references_from_context


def test_version():
    """Test version import."""
    from oarepo_references import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = OARepoReferences(app)
    assert 'oarepo-references' in app.extensions

    app = Flask('testapp')
    ext = OARepoReferences()
    assert 'oarepo-references' not in app.extensions
    ext.init_app(app)
    assert 'oarepo-references' in app.extensions


def test_signals():
    """Test if the signals are properly registered."""
    assert after_record_insert.has_receivers_for(create_references_record)
    assert after_marshmallow_validate.has_receivers_for(set_references_from_context)
