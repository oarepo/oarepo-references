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
from invenio_records.models import Timestamp
from invenio_search import current_search_client

from oarepo_references.models import RecordReference


class RecordReferenceAPI(object):
    """Represent a record reference.
    """
    indexer_version_type = None

    @classmethod
    def get_records(self, reference):
        """Retrieve multiple records by reference.

        :param reference: Reference URI
        :returns: A list of :class:`RecordReference` instances containing the reference.
        """
        with db.session.no_autoflush:
            query = RecordReference.query.filter(RecordReference.reference == reference)

            return query.all()

    @classmethod
    def reindex_referencing_records(self, reference):
        records = self.get_records(reference)
        RecordIndexer().bulk_index(records)
        RecordIndexer(version_type=self.indexer_version_type).process_bulk_queue(
            es_bulk_kwargs={'raise_on_error': True})
        current_search_client.indices.flush()

__all__ = (
    'RecordReferenceAPI',
)
