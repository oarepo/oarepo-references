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
from invenio_records.errors import MissingModelError
from invenio_records.signals import after_record_insert
from oarepo_validate import after_marshmallow_validate, before_marshmallow_validate

from oarepo_references.models import RecordReference
from oarepo_references.proxies import current_oarepo_references
from oarepo_references.utils import get_reference_uuid, keys_in_dict, \
    transform_dicts_in_data

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
    return record


@after_record_insert.connect
def create_references_record(sender, record, *args, **kwargs):
    """A signal receiver that creates record references on record create."""
    assert record.oarepo_references is not None,\
        "oarepo_references needs to be set on a record instance"

    with db.session.begin_nested():
        for ref in record.oarepo_references:
            RecordReference.create(record, **ref)

    db.session.commit()
