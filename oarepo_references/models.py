# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records"""

from __future__ import absolute_import, print_function

import uuid

from invenio_db import db
from invenio_records.models import Timestamp
from sqlalchemy import String, UniqueConstraint
from sqlalchemy_utils.types import UUIDType


class RecordReference(db.Model, Timestamp):
    """Represent a record references mapping entry.

    The RecordReference object contains a ``created`` and  a ``updated``
    timestamps that are automatically updated.
    """
    # Enables SQLAlchemy-Continuum versioning
    __versioned__ = {}

    __tablename__ = 'oarepo_records_references'

    __table_args__ = (UniqueConstraint('record_uuid', 'reference', name='_record_reference_uc'),)

    def __init__(self, record_uuid: uuid.UUID, reference: str):
        """Initialize record reference instance

        :param record_uuid: ID of an Invenio record
        :param reference: value of $ref reference
        """
        self.record_uuid = record_uuid
        self.reference = reference

    id = db.Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )
    """Internal DB Record identifier."""

    record_uuid = db.Column(
        UUIDType,
        index=True,
        nullable=False
    )
    """Invenio Record UUID indentifier"""

    reference = db.Column(
        String(255),
        index=True,
        nullable=False
    )
    """URI of the reference"""

    version_id = db.Column(db.Integer, nullable=False)
    """Used by SQLAlchemy for optimistic concurrency control."""

    __mapper_args__ = {
        'version_id_col': version_id
    }


__all__ = (
    'RecordReference',
)
