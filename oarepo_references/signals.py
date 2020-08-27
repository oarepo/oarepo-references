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
from oarepo_validate import after_marshmallow_validate

from oarepo_references.models import RecordReference
from oarepo_references.proxies import current_oarepo_references

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


@after_marshmallow_validate.connect
def set_references_from_context(sender, record, context, result, **kwargs):
    """A signal receiver to set record references from validation context."""
    record.oarepo_references = context.get('references', [])
    print('SETTING REFERENCE CONTEXT TO:', record.oarepo_references, record)
    return record


@after_record_insert.connect
def create_references_record(sender, record, *args, **kwargs):
    """A signal receiver that creates record references on record create."""
    assert record.oarepo_references is not None, \
        "oarepo_references needs to be set on a record instance"

    print('CREATE REFERENCE RECORDS FROM:', record.oarepo_references, record)
    with db.session.begin_nested():
        for ref in record.oarepo_references:
            RecordReference.create(record, **ref)

    db.session.commit()

    print('CURRENT REFERENCES:')
    for ref in RecordReference.query.all():
        print(ref)


@after_record_update.connect
def update_references_record(sender, record, *args, **kwargs):
    """A signal receiver that updates references records on record update."""
    assert record.canonical_url is not None, \
        'oarepo_references requires the canonical_url property on a record instance'

    return current_oarepo_references.reference_content_changed(record, record.canonical_url)


@after_record_delete.connect
def delete_references_record(sender, record, *args, **kwargs):
    """A signal receiver that deletes all reference records of a deleted Record."""
    return current_oarepo_references.delete_references_record(record)
