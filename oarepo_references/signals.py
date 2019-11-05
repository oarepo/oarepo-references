# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records"""

from __future__ import absolute_import, print_function

import uuid
from functools import wraps

from invenio_db import db
from invenio_records import Record
from invenio_records.errors import MissingModelError
from sqlalchemy.orm.exc import NoResultFound

from oarepo_references.models import RecordReference
from oarepo_references.utils import keys_in_dict


def pass_record(f):
    """Decorate to retrieve a record from event."""

    @wraps(f)
    def decorate(*args, **kwargs):
        rec = kwargs.pop('record', None)
        try:
            rid = rec.get('model').get('id')
            return f(record=rec, rid=rid, *args, **kwargs)
        except KeyError:
            return f(record=rec, *args, **kwargs)

    return decorate


@pass_record
def create_references_record(sender, record, rid=None, *args, **kwargs):
    if not rid: return

    try:
        refs = keys_in_dict(record)
        for ref in refs:
            rr = RecordReference(record_uuid=rid, reference=ref)
            # TODO: check for existence of this pair first
            db.session.add(rr)
            db.session.commit()
    except KeyError:
        raise MissingModelError()


@pass_record
def update_references_record(sender, record, rid=None, *args, **kwargs):
    # Find all entries for record id
    rrs = RecordReference.query.filter_by(record_uuid=rid)
    refs = keys_in_dict(record)

    # Delete removed/add added references
    with db.session.begin_nested():
        for rr in rrs.all():
            if rr.reference not in rrs:
                db.session.delete(rr)
        for ref in refs:
            if ref not in rrs.values('reference'):
                rr = RecordReference(record_uuid=rid, reference=ref)
                db.session.add(rr)

    db.session.commit()

@pass_record
def delete_references_record(sender, record, rid=None, *args, **kwargs):
    # Find all entries for record id and delete it
    RecordReference.query.filter_by(record_uuid=rid).delete()
