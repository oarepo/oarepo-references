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

from __future__ import absolute_import, print_function

import os

import pytest
from flask import Flask
from flask_babelex import Babel
from invenio_db import InvenioDB
from invenio_db import db as _db
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_records import Record, InvenioRecords
from invenio_search import InvenioSearch
from sqlalchemy_utils import database_exists, create_database

from oarepo_references import OARepoReferences


@pytest.fixture(scope='module')
def celery_config():
    """Override pytest-invenio fixture.

    TODO: Remove this fixture if you add Celery support.
    """
    return {}


@pytest.fixture(scope='module')
def create_app(instance_path):
    """Application factory fixture."""

    def factory(**config):
        app = Flask('testapp', instance_path=instance_path)
        app.config.update(
            TESTING=True,
            JSON_AS_ASCII=True,
            SQLALCHEMY_TRACK_MODIFICATIONS=True,
            SQLALCHEMY_DATABASE_URI=os.environ.get(
                'SQLALCHEMY_DATABASE_URI',
                'sqlite:///:memory:'),
            SERVER_NAME='localhost',
            SECURITY_PASSWORD_SALT='TEST_SECURITY_PASSWORD_SALT',
            SECRET_KEY='TEST_SECRET_KEY',
        )
        Babel(app)
        InvenioDB(app)
        InvenioJSONSchemas(app)
        InvenioRecords(app)
        InvenioSearch(app)
        OARepoReferences(app)
        return app

    return factory


@pytest.fixture
def db(app):
    """Create database for the tests."""
    with app.app_context():
        if not database_exists(str(_db.engine.url))\
           and app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite://':
            create_database(_db.engine.url)
        _db.create_all()

    yield _db

    # Explicitly close DB connection
    _db.session.close()
    _db.drop_all()


@pytest.fixture
def records(db):
    return [
        Record.create({'$ref': 'ref1'}),
        Record.create({'$ref': 'ref2'}),
        Record.create({'reflist': [
            {'$ref': 'ref3'},
            {'$ref': 'ref4'}
        ]})
    ]
