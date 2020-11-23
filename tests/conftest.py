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
import os
import uuid

import pytest
from flask import url_for
from invenio_app.factory import create_api
from invenio_db import db as _db
from invenio_pidstore.providers.recordid import RecordIdProvider
from sqlalchemy_utils import create_database, database_exists
from tests.test_utils import TestRecord

from oarepo_references.api import RecordReferenceAPI
from oarepo_references.models import ClassName


@pytest.fixture(scope="module")
def create_app():
    """Return API app."""
    return create_api


@pytest.fixture(scope="module")
def references_api():
    """Returns an instance of RecordReferenceAPI."""
    return RecordReferenceAPI()


@pytest.fixture(scope='session')
def celery_config():
    """Celery app test configuration."""
    return {
        'broker_url': 'memory://localhost/',
        'result_backend': 'rpc'
    }


@pytest.fixture(scope="module")
def app_config(app_config):
    """Flask application fixture."""
    app_config = dict(
        TESTING=True,
        JSON_AS_ASCII=True,
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI',
            'sqlite:///:memory:'),
        SERVER_NAME='localhost',
        CELERY_ALWAYS_EAGER=True,
        CELERY_BROKER_URL='memory://localhost/',
        CELERY_RESULT_BACKEND='rpc'
    )
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
def db(app):
    """Returns fresh db."""
    with app.app_context():
        if not database_exists(str(_db.engine.url)) and \
          app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite://':
            create_database(_db.engine.url)
        _db.create_all()

    yield _db

    # Explicitly close DB connection
    _db.session.close()
    _db.drop_all()


def get_pid():
    """Generates a new PID for a record."""
    record_uuid = uuid.uuid4()
    provider = RecordIdProvider.create(
        object_type='rec',
        object_uuid=record_uuid,
    )
    return record_uuid, provider.pid.pid_value


@pytest.fixture
def referenced_records(db):
    """Create a list of records to be referenced by other records."""
    rrdata = [{'title': 'a'}, {'title': 'b'}]
    referenced_records = []

    for rr in rrdata:
        ruuid, pid = get_pid()
        rr['pid'] = pid
        referenced_records.append(TestRecord.create(rr, id_=ruuid))

    db.session.commit()
    return referenced_records


def get_ref_url(pid):
    """Returns canonical_url for a record by its PID."""
    return url_for('invenio_records_rest.recid_item',
                   pid_value=pid, _external=True)


@pytest.fixture
def class_names(db):
    """Test Class names fixture."""
    class_names = [
        ClassName.create(name=str(TestRecord.__class__))
    ]

    db.session.commit()
    return class_names


@pytest.fixture
def referencing_records(db, referenced_records):
    """Create sample records with references to others."""
    referencing_records = [
        TestRecord.create({
            'title': 'c',
            'pid': get_pid()[1],
            '$ref': get_ref_url(referenced_records[0]['pid'])
        }),
        TestRecord.create({
            'title': 'd',
            'pid': get_pid()[1],
            '$ref': get_ref_url(referenced_records[1]['pid'])
        }),
        TestRecord.create({'title': 'e',
                           'pid': get_pid()[1],
                           'reflist': [
                               {'$ref': get_ref_url(referenced_records[1]['pid'])},
                               {'$ref': get_ref_url(referenced_records[0]['pid'])}
                           ]}),
        TestRecord.create({'title': 'f',
                           'pid': get_pid()[1],
                           'reflist': [
                               {'title': 'f', '$ref': get_ref_url(referenced_records[0]['pid'])},
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
