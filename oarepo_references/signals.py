# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records."""

from __future__ import absolute_import, print_function

from blinker import Namespace
from invenio_db import db
from invenio_records.signals import after_record_delete, after_record_insert, \
    after_record_update
from oarepo_validate import before_marshmallow_validate, after_marshmallow_validate

from oarepo_references.models import RecordReference
from oarepo_references.proxies import current_references

_signals = Namespace()

after_reference_update = _signals.signal('after-reference-update')
"""Signal sent after a reference is updated.

When implementing the event listener, the referencing record ids
can retrieved from `kwarg['references']`, the referenced object
can be retrieved from `sender`, the referenced record can be retrieved
from `kwarg['record']`.

.. note::

   Do not perform any modification to the referenced object here:
   they will be not persisted.
"""


@before_marshmallow_validate.connect
def set_references_to_context(sender, context, **kwargs):
    """A signal receiver to set record references from validation context."""
    if 'references' not in context:
        context['references'] = []


@after_marshmallow_validate.connect
def set_references_from_context(sender, record, context, result, **kwargs):
    """A signal receiver to set record references from validation context."""
    record.oarepo_references = context.get('references', [])
    return record


@after_record_insert.connect
def create_references_record(sender, record, *args, **kwargs):
    """A signal receiver that creates record references on record create."""
    assert record.oarepo_references is not None, \
        "oarepo_references needs to be set on a record instance"
    with db.session.begin_nested():
        RecordReference.update_references(record, record.oarepo_references)


@after_record_update.connect
def update_references_record(sender, record, *args, **kwargs):
    """A signal receiver that updates references records on record update."""
    assert record.canonical_url is not None, \
        'oarepo_references requires the canonical_url property on a record instance'

    with db.session.begin_nested():
        RecordReference.update_references(record, record.oarepo_references)
        return current_references.reference_content_changed(record, record.canonical_url)


@after_record_delete.connect
def delete_references_record(sender, record, *args, **kwargs):
    """A signal receiver that deletes all reference records of a deleted Record."""
    return current_references.delete_references_record(record)
