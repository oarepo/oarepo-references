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
from invenio_records import Record
from invenio_records.models import Timestamp
from sqlalchemy import Boolean, Integer, String, UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy_utils.types import UUIDType

from oarepo_references.utils import class_import_string, get_record_object


class ClassName(db.Model, Timestamp):
    """Represents a record class lookup table."""

    __tablename__ = 'oarepo_references_classname'

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String, index=True, unique=True)

    def __init__(self, name):
        """Initialize ClassName instance."""
        self.name = name

    @classmethod
    def create(cls, name):
        """Create a ClassName instance."""
        with db.session.begin_nested():
            ret = cls(name=name)
            db.session.add(ret)
            return ret


class ReferencingRecord(db.Model, Timestamp):
    """Represents a lookup table for classes of referencing records."""

    __tablename__ = 'oarepo_references_referencing_record'

    def __init__(self,
                 record_uuid: uuid.UUID,
                 class_name: ClassName):
        """Initialize record reference instance."""
        self.record_uuid = record_uuid
        self.class_name = class_name

    @classmethod
    def create(cls, record_uuid, class_name):
        """
        Create a new ReferencingRecord.

        :param record_uuid: UUID of the referencing record
        :param class_id: reference to a class of a referencing record
        :return an instance of a created ReferencingRecord
        """
        with db.session.begin_nested():
            ret = cls(record_uuid=record_uuid, class_name=class_name)
            db.session.add(ret)
            return ret

    id = db.Column(Integer, primary_key=True)
    record_uuid = db.Column(
        UUIDType,
        index=True,
        unique=True,
        nullable=True
    )
    references = relationship('RecordReference',
                              backref='record',
                              cascade="all, delete",
                              passive_deletes=True)
    class_id = db.Column(Integer,
                         db.ForeignKey(
                             ClassName.id,
                             name='fk_oarepo_references_class_id_classname',
                             ondelete='CASCADE'
                         ))
    class_name = relationship('ClassName', cascade="all, delete", passive_deletes=True)


class RecordReference(db.Model, Timestamp):
    """
    Represent a record references mapping entry.

    The RecordReference object contains a ``created`` and  a ``updated``
    timestamps that are automatically updated.
    """

    # Enables SQLAlchemy-Continuum versioning
    __versioned__ = {}

    __tablename__ = 'oarepo_references'
    __table_args__ = (UniqueConstraint('record_id',
                                       'reference',
                                       name='uq_oarepo_references_record_id_reference'),)

    def __init__(self,
                 record: ReferencingRecord,
                 reference: str,
                 reference_uuid: uuid.UUID,
                 inline: bool):
        """Initialize record reference instance.

        :param record: instance of a referencing Invenio record
        :param reference: URL of a referenced object
        :param reference_uuid: UUID of a referenced object (optional)
        :param inline: Referenced object data inlined into referencing record?
        """
        self.record = record
        self.reference = reference
        self.reference_uuid = reference_uuid
        self.inline = inline

    @classmethod
    def create(cls, record: Record, reference, reference_uuid, inline=False, raise_on_duplicit=True):
        """Creates a new Reference Record.

        :param record: an Invenio Record instance
        :param reference: URL reference to the referenced object
        :param reference_uuid: UUID of the referenced object
        :param inline: is referenced object data inlined into the referencing record?
        :return: an instance of the created RecordReference
        """
        if RecordReference.query \
            .join(ReferencingRecord, aliased=True) \
            .filter(ReferencingRecord.record_uuid == record.id) \
            .filter(RecordReference.reference == reference).count() > 0:
            if raise_on_duplicit:
                raise IntegrityError('Error creating reference record - already exists', '', [], None)
            return None
        with db.session.begin_nested():
            reccls = str(class_import_string(record))
            try:
                cn = ClassName.query.filter_by(name=reccls).one()
            except NoResultFound:
                cn = ClassName.create(reccls)

            try:
                rr = ReferencingRecord.query.filter_by(record_uuid=record.id).one()
            except NoResultFound:
                rr = ReferencingRecord.create(record.id, cn)

            ret = cls(
                record=rr,
                reference=reference,
                reference_uuid=reference_uuid,
                inline=inline)

            db.session.add(ret)
            return ret

    @classmethod
    def update_references(cls, record, references):

        refs = {}
        for ref in (references or []):
            refs[ref['reference']] = ref

        refs_set = set(refs.keys())

        existing_refs = set(
            ref.reference
            for ref in RecordReference.query \
                .join(ReferencingRecord, aliased=True) \
                .filter(ReferencingRecord.record_uuid == record.id)
        )

        new_refs = refs_set - existing_refs
        obsolete_refs = existing_refs - refs_set

        for ref_key in new_refs:
            RecordReference.create(record, **refs[ref_key])

        if obsolete_refs:
            for x in \
                RecordReference.query \
                    .join(ReferencingRecord, aliased=True) \
                    .filter(ReferencingRecord.record_uuid == record.id) \
                    .filter(RecordReference.reference.in_(obsolete_refs)):
                db.session.delete(x)

    id = db.Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )
    """Internal DB Record identifier."""

    record_id = db.Column(
        db.ForeignKey(ReferencingRecord.id,
                      name='fk_oarepo_references_record_id_record',
                      ondelete="CASCADE")
    )
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
        Boolean(name='ck_oarepo_references_inline'),
        default=False
    )

    version_id = db.Column(db.Integer, nullable=False)
    """Used by SQLAlchemy for optimistic concurrency control."""

    __mapper_args__ = {
        'version_id_col': version_id
    }

    def __repr__(self):
        """Reference Record representation string."""
        return f'{get_record_object(self)}->{self.reference}'


__all__ = (
    'RecordReference',
    'ReferencingRecord',
    'ClassName'
)
