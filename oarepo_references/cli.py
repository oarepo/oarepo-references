import click
from flask.cli import with_appcontext
from invenio_db import db
from invenio_records import Record
from invenio_records.models import RecordMetadata

from oarepo_references.proxies import current_oarepo_references
from oarepo_references.utils import transform_dicts_in_data
from .signals import update_references_record, convert_taxonomy_refs


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
    for rec in records:
        click.echo('Updating reference records for record: {}'.format(rec.id))
        transform_dicts_in_data(rec, convert_taxonomy_refs)
        current_oarepo_references.update_references_from_record(rec)
