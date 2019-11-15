# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records"""

from __future__ import absolute_import, print_function

from invenio_db import db
from invenio_records.models import Timestamp

from oarepo_references.models import RecordReference


class RecordReferenceAPI(db.Model, Timestamp):
    """Represent a record reference.
    """
    @classmethod
    def get_records(self, reference):
        """Retrieve multiple records by reference.

        :param reference: Reference URI
        :returns: A list of :class:`RecordReference` instances containing the reference.
        """
        with db.session.no_autoflush:
            query = RecordReference.query.filter(RecordReference.reference == reference)

            return query.all()


__all__ = (
    'RecordReferenceAPI',
)
