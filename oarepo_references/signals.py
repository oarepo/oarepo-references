# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records"""

from __future__ import absolute_import, print_function

from invenio_records.errors import MissingModelError
from oarepo_references.models import RecordReferences
from oarepo_references.utils import keys_in_dict


def create_references_record(sender, *args, **kwargs):
    rid = None

    if 'record' in kwargs:
        rec = kwargs['record']
        try:
            rid = rec['model']['id']
            refs = keys_in_dict(rec)
            for ref in refs:
                rr = RecordReferences(record_uuid=rid, reference=ref)
        except KeyError:
            raise MissingModelError()


    print(**kwargs)


def update_references_record(sender, *args, **kwargs):
    print(**kwargs)


def delete_references_record(sender, *args, **kwargs):
    print(**kwargs)
