# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""
import uuid

import pytest
from flask import url_for
from invenio_app.factory import create_api
from invenio_pidstore.providers.recordid import RecordIdProvider
from invenio_records import Record

from oarepo_references.api import RecordReferenceAPI


@pytest.fixture(scope="module")
def create_app():
    """Return API app."""
    return create_api


@pytest.fixture(scope="module")
def references_api():
    """Returns an instance of RecordReferenceAPI."""
    return RecordReferenceAPI()


@pytest.fixture(scope="module")
def app_config(app_config):
    """Flask application fixture."""
    app_config['SERVER_NAME'] = 'localhost'
    app_config['PIDSTORE_RECID_FIELD'] = 'pid'
    app_config['RECORDS_REST_ENDPOINTS'] = dict(
        recid=dict(
            pid_type='recid',
            pid_minter='recid',
            pid_fetcher='recid',
            record_serializers={
                'application/json': ('invenio_records_rest.serializers'
                                     ':json_v1_response'),
            },
            search_serializers={
                'application/json': ('invenio_records_rest.serializers'
                                     ':json_v1_search'),
            },
            list_route='/records/',
            item_route='/records/<pid(recid):pid_value>'
        )
    )
    return app_config


@pytest.fixture
def referenced_records(db):
    """Create a list of records to be referenced by other records."""
    rrdata = [{'title': 'a'}, {'title': 'b'}]
    referenced_records = []

    for rr in rrdata:
        record_uuid = uuid.uuid4()
        provider = RecordIdProvider.create(
            object_type='rec',
            object_uuid=record_uuid,
        )
        rr["pid"] = provider.pid.pid_value
        referenced_records.append(Record.create(rr, id_=record_uuid))

    db.session.commit()
    return referenced_records


@pytest.fixture
def referencing_records(db, referenced_records):
    """Create sample records with references to others."""

    def _get_ref_url(pid):
        return url_for('invenio_records_rest.recid_item',
                       pid_value=pid, _external=True)

    referencing_records = [
        Record.create({
            'title': 'c',
            '$ref': _get_ref_url(referenced_records[0]['pid'])
        }),
        Record.create({
            'title': 'd',
            '$ref': _get_ref_url(referenced_records[1]['pid'])
        }),
        Record.create({'title': 'e', 'reflist': [
            {'$ref': _get_ref_url(referenced_records[1]['pid'])},
            {'$ref': _get_ref_url(referenced_records[0]['pid'])}
        ]}),
        Record.create({'title': 'f', 'reflist': [
            {'title': 'f', '$ref': _get_ref_url(referenced_records[0]['pid'])},
        ]})
    ]
    db.session.commit()

    return referencing_records


@pytest.fixture
def test_record_data():
    """Returns a data for a test record."""
    return {
        'pid': 999,
        'title': 'rec1',
        'taxo1': {
            'links': {
                'self': 'http://localhost/api/taxonomies/requestors/a/b/',
            },
            'slug': 'b'
        },
        'sub': {
            'taxo2': {
                'links': {
                    'self': 'http://localhost/api/taxonomies/requestors/a/c/',
                },
                'slug': 'c'
            }
        }
    }
