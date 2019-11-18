import click
from flask.cli import with_appcontext
from invenio_db import db
from invenio_records import Record
from invenio_records.models import RecordMetadata

from oarepo_references.proxies import current_oarepo_references
from .signals import update_references_record

@click.group()
def references():
    """OArepo references."""


#
# References subcommands
#
@references.command('synchronize')
@with_appcontext
def synchronize():
    """Scan all records and update references table."""
    rms = [v for v, in db.session.query(RecordMetadata.id).all()]
    records = Record.get_records(rms)
    click.echo('Updating reference records for records: {}'.format(records))
    for rec in records:
        current_oarepo_references.update_references_from_record(rec)
