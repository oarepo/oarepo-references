# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Minimal Flask application example.

SPHINX-START

First install oarepo-references, setup the application and load
fixture data by running:

.. code-block:: console

   $ pip install -e .[all]
   $ cd examples
   $ ./app-setup.sh
   $ ./app-fixtures.sh

Next, start the development server:

.. code-block:: console

   $ export FLASK_APP=app.py FLASK_DEBUG=1
   $ flask run

and open the example application in your browser:

.. code-block:: console

    $ open http://127.0.0.1:5000/

To reset the example application run:

.. code-block:: console

    $ ./app-teardown.sh

SPHINX-END
"""

from __future__ import absolute_import, print_function

import os

from flask import Flask, url_for
from flask_babelex import Babel
from invenio_records import Record
from marshmallow import INCLUDE, Schema
from marshmallow.fields import URL, Field
from oarepo_validate import MarshmallowValidatedRecordMixin

from oarepo_references import OARepoReferences
from oarepo_references.mixins import InlineReferenceMixin, \
    ReferenceByLinkFieldMixin, ReferenceEnabledRecordMixin


class ExampleURLReferenceField(ReferenceByLinkFieldMixin, URL):
    """URL reference marshmallow field."""


class ExampleLinksField(Field):
    """Taxonomy links field."""
    self = ExampleURLReferenceField()


class ExampleInlineReferenceSchema(InlineReferenceMixin, Schema):
    """Taxonomy schema."""

    class Meta:
        unknown = INCLUDE

    def ref_url(self, data):
        return data.get('links', {}).get('self', None)


class ExampleRecord(MarshmallowValidatedRecordMixin,
                    ReferenceEnabledRecordMixin,
                    Record):
    """References enabled example record class."""
    MARSHMALLOW_SCHEMA = ExampleInlineReferenceSchema
    VALIDATE_MARSHMALLOW = True
    VALIDATE_PATCH = True

    @property
    def canonical_url(self):
        return url_for('invenio_records_rest.recid_item',
                       pid_value=self['pid'], _external=True)


# Create Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', "sqlite:///:memory:")
app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME', '127.0.0.1:5000')
app.config['PREFERRED_URL_SCHEME'] = 'http'
app.config["SQLALCHEMY_ECHO"] = True
Babel(app)
OARepoReferences(app)
