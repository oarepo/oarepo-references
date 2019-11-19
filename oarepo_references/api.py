# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records"""

from __future__ import absolute_import, print_function

from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_records import Record
from invenio_records.models import Timestamp
from invenio_search import current_search_client

from oarepo_references.models import RecordReference
from oarepo_references.signals import after_reference_update
from oarepo_references.utils import keys_in_dict


class RecordReferenceAPI(object):
    """Represent a record reference.
    """
    indexer_version_type = None

    @classmethod
    def get_records(cls, reference, exact=False):
        """Retrieve multiple records by reference.

        :param reference: Reference URI
        :returns: A list of :class:`RecordReference` instances containing the reference.
        """
        with db.session.no_autoflush:
            if exact:
                query = RecordReference.query\
                    .filter(RecordReference.reference == reference)\
                    .distinct(RecordReference.record_uuid)
            else:
                query = RecordReference.query\
                    .filter(RecordReference.reference.startswith(reference))\
                    .distinct(RecordReference.record_uuid)

            return query.all()

    @classmethod
    def reindex_referencing_records(cls, ref=None, record=None):
        if not (ref or record):
            raise AttributeError('Reference link or record must be provided')

        recids = []
        sender = None
        if ref:
            refs = cls.get_records(ref)
            records = Record.get_records([r.record_uuid for r in refs])
            recids = [r.id for r in records]
            sender = ref

        if record:
            # TODO: how to find referencing records given a base record instance
            recids.append(record.id)
            sender = record

        indexed = after_reference_update.send(sender, references=recids, record=record)
        print('reference_update_reindex_handled', indexed)
        if not any([res[1] for res in indexed]):
            RecordIndexer().bulk_index(recids)
            RecordIndexer(version_type=cls.indexer_version_type).process_bulk_queue(
            es_bulk_kwargs={'raise_on_error': True})
            current_search_client.indices.flush()

    @classmethod
    def update_references_from_record(cls, record):
        # Find all entries for record id
        rrs = RecordReference.query.filter_by(record_uuid=record.model.id)
        rec_refs = list(set(list(keys_in_dict(record))))
        db_refs = list(set([r[0] for r in rrs.values('reference')]))

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


__all__ = (
    'RecordReferenceAPI',
)
