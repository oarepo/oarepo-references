# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records."""

from __future__ import absolute_import, print_function

from invenio_base.utils import obj_or_import_string
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_records import Record
from invenio_search import current_search_client

from oarepo_references.mixins import ReferenceEnabledRecordMixin
from oarepo_references.models import RecordReference, ReferencingRecord
from oarepo_references.signals import after_reference_update
from oarepo_references.utils import get_record_object


class RecordReferenceAPI(object):
    """Represent a record reference."""

    indexer_version_type = None

    @classmethod
    def reference_content_changed(cls, ref_obj, ref_url=None, ref_uuid=None):
        """Find & update records that have inlined the changed reference."""
        assert ref_url or ref_uuid, 'Reference URL or UUID must be provided'

        updated = []

        records_to_update = cls.get_records(ref_url, exact=True)
        for r in records_to_update:
            rec = get_record_object(r)
            if isinstance(rec, ReferenceEnabledRecordMixin):
                rec.update_inlined_ref(ref_url, ref_uuid, ref_obj)
                updated.append(rec)

        return updated

    @classmethod
    def reference_changed(cls, old, new):
        records_to_update = cls.get_records(old, exact=True)

    @classmethod
    def get_records(cls, reference, exact=False):
        """Retrieve multiple reference records by reference.

        :param reference: Reference URI
        :returns: A list of :class:`oarepo_references.models.RecordReference`
                  instances containing the reference.
        """
        with db.session.no_autoflush:
            if exact:
                query = RecordReference.query \
                    .filter(RecordReference.reference == reference)
            else:
                query = RecordReference.query \
                    .filter(RecordReference.reference.startswith(reference))

        return query.all()

    @classmethod
    def reindex_referencing_records(cls, ref, ref_obj=None):
        """
        Reindex all records that reference given object or string reference.

        :param ref:         string reference to be checked
        :param ref_obj:     an object (record etc.) of the reference
        """
        refs = cls.get_records(ref)
        records = Record.get_records([r.record.record_uuid for r in refs])
        recids = [r.id for r in records]
        sender = ref_obj if ref_obj else ref
        indexed = after_reference_update.send(sender, references=recids, ref_obj=ref_obj)
        if not any([res[1] for res in indexed]):
            RecordIndexer().bulk_index(recids)
            RecordIndexer(version_type=cls.indexer_version_type).process_bulk_queue(
                es_bulk_kwargs={'raise_on_error': True})
            current_search_client.indices.flush()

    @classmethod
    def update_references_from_record(cls, record):
        """
        Gathers all references from a record and updates internal RecordReference table.

        :param record invenio record
        """
        with db.session.begin_nested():
            # Find all entries for record id
            rr = ReferencingRecord.query.filter_by(record_uuid=record.model.id).one()
            record.validate()


__all__ = (
    'RecordReferenceAPI',
)
