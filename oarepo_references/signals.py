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


def convert_taxonomy_refs(in_data):
    """
    Replaces self links with $ref.

    This function checks if the in_data contains links/self
    and if found replaces the element with $ref.

    :param in_data: the incoming data
    :return:    either the incoming data or element with $ref
    """
    self_link = in_data.get('links', {}).get('self', None)
    if self_link and 'slug' in in_data:
        return {
            '$ref': in_data['links']['self']
        }
    return in_data


def convert_record_refs(sender, record, *args, **kwargs):
    """A signal receiver to transform self links to $ref."""
    transform_dicts_in_data(record, convert_taxonomy_refs)


def create_references_record(sender, record, *args, **kwargs):
    """A signal receiver that creates record references on record create."""
    try:
        refs = keys_in_dict(record, required_types=(str,))
        for ref in refs:
            ref_uuid = get_reference_uuid(ref)
            with db.session.begin_nested():
                rr = RecordReference(record_uuid=record.model.id,
                                     reference=ref,
                                     reference_uuid=ref_uuid)
                # TODO: check for existence of this pair first
                db.session.add(rr)
    except KeyError:
        raise MissingModelError()


def update_references_record(sender, record, *args, **kwargs):
    """A signal receiver that updates referencing objects on record update."""
    current_oarepo_references.update_references_from_record(record)
    if hasattr(record, 'canonical_url'):
        ref = record.canonical_url
    else:
        raise AttributeError('missing canonical_url on record')
    current_oarepo_references.reindex_referencing_records(ref=ref, ref_obj=record)


def delete_references_record(sender, record, *args, **kwargs):
    """A signal receiver that removes references on record delete."""
    # Find all entries for record id and delete it
    RecordReference.query.filter_by(record_uuid=record.model.id).delete()
