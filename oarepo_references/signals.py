# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records"""

from __future__ import absolute_import, print_function

from invenio_db import db
from invenio_records.errors import MissingModelError

from flask_taxonomies.marshmallow import TaxonomySchemaV1
from oarepo_references.models import RecordReference
from oarepo_references.utils import keys_in_dict, transform_dicts_in_data


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
    # Find all entries for record id
    rrs = RecordReference.query.filter_by(record_uuid=record.model.id)
    rec_refs = list(keys_in_dict(record))
    db_refs = [r[0] for r in rrs.values('reference')]

    record.validate()

    # Delete removed/add added references
    with db.session.begin_nested():
        for rr in rrs.all():
            if rr.reference not in rec_refs:
                db.session.delete(rr)
        for ref in rec_refs:
            if ref not in db_refs:
                rr = RecordReference(record_uuid=record.model.id, reference=ref)
                db.session.add(rr)

    db.session.commit()


def delete_references_record(sender, record, *args, **kwargs):
    # Find all entries for record id and delete it
    RecordReference.query.filter_by(record_uuid=record.model.id).delete()
