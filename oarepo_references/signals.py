# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records"""

from __future__ import absolute_import, print_function

from blinker import Namespace
from invenio_db import db
from invenio_records.errors import MissingModelError

from flask_taxonomies.marshmallow import TaxonomySchemaV1
from oarepo_references.models import RecordReference
from oarepo_references.proxies import current_oarepo_references
from oarepo_references.utils import keys_in_dict, transform_dicts_in_data

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


def convert_taxonomy_refs(in_data):
    try:
        result = TaxonomySchemaV1().load(in_data)
        if not result.errors:
            return result.data
    except ValueError:
        pass

    return in_data


def convert_record_refs(sender, record, *args, **kwargs):
    transform_dicts_in_data(record, convert_taxonomy_refs)


def create_references_record(sender, record, *args, **kwargs):
    try:
        refs = keys_in_dict(record)
        for ref in refs:
            rr = RecordReference(record_uuid=record.model.id, reference=ref)
            # TODO: check for existence of this pair first
            db.session.add(rr)
            db.session.commit()
    except KeyError:
        raise MissingModelError()


def update_references_record(sender, record, *args, **kwargs):
    current_oarepo_references.update_references_from_record(record)
    current_oarepo_references.reindex_referencing_records(record=record)


def delete_references_record(sender, record, *args, **kwargs):
    # Find all entries for record id and delete it
    RecordReference.query.filter_by(record_uuid=record.model.id).delete()
