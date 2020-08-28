# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records."""

import click
from flask.cli import with_appcontext
from invenio_db import db
from invenio_records import Record
from invenio_records.models import RecordMetadata

from oarepo_references.models import RecordReference
from oarepo_references.proxies import current_references


@click.group()
def references():
    """References support for OArepo."""


#
# References subcommands
#
@references.command('synchronize')
@click.option('--clear/--no-clear', default=False)
@with_appcontext
def synchronize(clear):
    """Scan all records and update references table."""
    rms = [v for v, in db.session.query(RecordMetadata.id).all()]
    records = Record.get_records(rms)
    if clear:
        RecordReference.query.delete()

    for rec in records:
        click.echo('Updating reference records for record: {}'.format(rec.id))
        current_references.update_references_from_record(rec)
