# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records."""

from __future__ import absolute_import, print_function

import uuid

from invenio_db import db
from invenio_records.models import Timestamp
from sqlalchemy import String, UniqueConstraint, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlalchemy_utils.types import UUIDType


class ClassName(db.Model, Timestamp):
    """
    Represents a record class lookup table.
    """
    __tablename__ = 'oarepo_references_classname'
    __table_args__ = (UniqueConstraint('name'),)

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String)


class ReferencingRecord(db.Model, Timestamp):
    """
    Represents a lookup table for classes of referencing records.
    """
    __tablename__ = 'oarepo_references_referencing_record'
    __table_args__ = (UniqueConstraint('record_uuid'),)

    id = db.Column(Integer, primary_key=True)
    record_uuid = db.Column(
        UUIDType,
        index=True,
        nullable=True
    )
    class_id = db.Column(Integer, db.ForeignKey(ClassName.id))
    class_name = relationship('ClassName', foreign_keys='ClassName.class_id')


class RecordReference(db.Model, Timestamp):
    """
    Represent a record references mapping entry.

    The RecordReference object contains a ``created`` and  a ``updated``
    timestamps that are automatically updated.
    """

    # Enables SQLAlchemy-Continuum versioning
    __versioned__ = {}

    __tablename__ = 'oarepo_references'

    __table_args__ = (UniqueConstraint('record_uuid', 'reference', name='_record_reference_uc'),)

    def __init__(self,
                 record_uuid: uuid.UUID,
                 reference: str,
                 reference_uuid: uuid.UUID,
                 inline: bool):
        """Initialize record reference instance.

        :param record_uuid: UUID of a referencing Invenio record
        :param reference: URL of a referenced object
        :param reference_uuid: UUID of a referenced object (optional)
        :param inline: Referenced object data inlined into referencing record?
        """
        self.record_uuid = record_uuid
        self.reference = reference
        self.reference_uuid = reference_uuid
        self.inline = inline

    id = db.Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )
    """Internal DB Record identifier."""

    record_id = db.Column(db.ForeignKey(ReferencingRecord.id))
    record = relationship('ReferencingRecord', foreign_keys='RecordReference.record_id')
    """Invenio Referencing Record info"""

    reference = db.Column(
        String(255),
        index=True,
        nullable=False
    )
    """URI of the reference"""

    reference_uuid = db.Column(
        UUIDType,
        index=True,
        nullable=True
    )
    """Invenio Record UUID indentifier of the referenced object
    in case the object is an invenio record"""

    inline = db.Column(
        Boolean,
        default=False
    )

    version_id = db.Column(db.Integer, nullable=False)
    """Used by SQLAlchemy for optimistic concurrency control."""

    __mapper_args__ = {
        'version_id_col': version_id
    }


__all__ = (
    'RecordReference',
    'ReferencingRecord',
    'ClassName'
)
