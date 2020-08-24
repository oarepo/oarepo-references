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
import typing

from flask import Flask
from flask_babelex import Babel
from invenio_records import Record
from invenio_records_rest.schemas.fields import SanitizedUnicode
from marshmallow import Schema, missing, post_load
from marshmallow.fields import URL, Field
from oarepo_validate import MarshmallowValidatedRecordMixin

from oarepo_references import OARepoReferences
from oarepo_references.mixins import ReferenceEnabledRecordMixin
from oarepo_references.schemas.fields.reference import ReferenceFieldMixin


class ExampleURLReferenceField(ReferenceFieldMixin, URL):
    """URL reference marshmallow field."""

    def deserialize(self,
                    value: typing.Any,
                    attr: str = None,
                    data: typing.Mapping[str, typing.Any] = None,
                    **kwargs):
        output = super(ExampleURLReferenceField, self).deserialize(value, attr, data, **kwargs)
        if output is missing:
            return output
        changes = self.context.get('changed_reference', None)
        # TODO: update value if the changes are related to this instance
        self.register(output, None, False)
        return output


class ExampleLinksField(Field):
    """Taxonomy links field."""
    self = ExampleURLReferenceField()


class ExampleReferenceSchema(Schema):
    """Taxonomy schema."""
    links = ExampleLinksField()
    slug = SanitizedUnicode()

    @post_load
    def update_inline_changes(self, data, many, **kwargs):
        changes = self.context.get('changed_reference', None)
        if changes and changes['url'] == self.self_url(data):
            data = changes['content']
        return data

    @classmethod
    def self_url(cls, data):
        return data.get('links', {}).get('self', None)


class ExampleRecord(MarshmallowValidatedRecordMixin,
                    ReferenceEnabledRecordMixin,
                    Record):
    """References enabled example record class."""
    MARSHMALLOW_SCHEMA = ExampleReferenceSchema
    VALIDATE_MARSHMALLOW = True
    VALIDATE_PATCH = True


# Create Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', "sqlite:///:memory:")
app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME', '127.0.0.1:5000')
app.config['PREFERRED_URL_SCHEME'] = 'http'
app.config["SQLALCHEMY_ECHO"] = True
Babel(app)
OARepoReferences(app)
