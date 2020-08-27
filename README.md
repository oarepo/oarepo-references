# OArepo references

[![](https://img.shields.io/github/license/oarepo/flask-taxonomies.svg)](https://github.com/oarepo/flask-taxonomies/blob/master/LICENSE)
[![](https://img.shields.io/travis/oarepo/flask-taxonomies.svg)](https://travis-ci.org/oarepo/flask-taxonomies)
[![](https://img.shields.io/coveralls/oarepo/flask-taxonomies.svg)](https://coveralls.io/r/oarepo/flask-taxonomies)
[![](https://img.shields.io/pypi/v/flask-taxonomies.svg)](https://pypi.org/pypi/flask-taxonomies)

OArepo module for tracking and updating references in Invenio records

## Installation

To use this module in your Invenio application, run the following in your virtual environment:
```console
    pip install oarepo-references
```

## Prerequisites

- [oarepo-validate](https://github.com/oarepo/oarepo-validate)

This module expects a `canonical_url` field present on your Record model. This field
should contain a full canonical url reference to the Record instance, e.g.

```python
class Record(FilesRecord):
    @property
    def canonical_url(self):
        return url_for('invenio_records_rest.recid_item',
                       pid_value=self['pid'], _external=True)
```

## Types of reference

This module considers the following two types of reference that can occur
the referencing objects:

### Reference by link

Reference to another object is represented in the referencing
object's metadata as a `canonical_url` of the referenced object, e.g:

```json
{
...
  "links": {
    "attachments": "https://example.org/objects/M249/attachments",
    "self": "https://example.org/objects/M249",
    "works": "https://example.org/objects/M249/works"
  }
}
```

### Inlined reference

The actual metadata content of the referenced object are inlined
into the referencing object's metadata, e.g:

```json
{
  ...
    "stylePeriod": {
        "id":	123,
        "level": 1,
        "links": {…},
        "path": "/novovek-moderni-doba",
        "slug":	"novovek-moderni-doba",
        "startYear": 1789,
        "title": […],
        "tooltip": ""
    }
}
```

In the example above, the complete metadata of a certain Taxonomic record
are inlined into the `stylePeriod` field of the referencing object.

## Usage

To enable reference tracking on your data model objects, you will need to
do the following:

  - Tell Marshmallow, which fields of your marshmallow schema contain references
     by inheriting `ReferenceByLinkFieldMixin`:

```
class URLReferenceField(ReferenceByLinkFieldMixin, URL):
    """URL reference marshmallow field."""
```

  - If the field holds *inlined* reference, use more generic `ReferenceFieldMixin`
    and override the `deserialize` method like this:

```
def deserialize(self,
                value: typing.Any,
                attr: str = None,
                data: typing.Mapping[str, typing.Any] = None,
                **kwargs):
        changes = self.context.get('changed_reference', None)
        # TODO: check if changes['url'] or changes['uuid']
        # refers to the current value and if so, update it
        # with changes['content']

        output = super(ReferenceByLinkFieldMixin, self).deserialize(value, attr, data, **kwargs)
        if output is missing:
            return output

        # TODO: determine canonical_url or object uuid from the output
        # to be used for reference registration
        self.register(output, None, False)
        return output
```

  - Use the reference-enabled field in your Marshmallow schema:
```
class ExampleReferenceSchema(Schema):
    """Link to other object schema."""
    link = URLReferenceField()
```

  - Inherit your Record model from the `ReferenceEnabledRecordMixin` and `MarshmallowValidatedRecordMixin`.
    Doing so, will add support for automatic Record updates whenever some reference contained in Record metadata
    changes:

```
class ExampleRecord(MarshmallowValidatedRecordMixin,
                    ReferenceEnabledRecordMixin,
                    Record):
    """References enabled example record class."""
    MARSHMALLOW_SCHEMA = ExampleReferenceSchema
    VALIDATE_MARSHMALLOW = True
    VALIDATE_PATCH = True

    @property
    def canonical_url(self):
        return url_for('invenio_records_rest.recid_item',
                       pid_value=self['pid'], _external=True)
```

## Signals

This module will register the following signal handlers on the Invenio Records signals that handle
managing of reference records whenever a Record changes:

| Invenio Records signal | Registered [signal handler](https://github.com/oarepo/oarepo-references/blob/master/oarepo_references/signals.py) | Description |
|------------------------|--------------------------|----------------------------------------------------------------------------------------------------------|
| after_record_insert    | create_references_record | Finds all references to other objects in a Record and creates RecordReference entries for each reference |
| after_record_update    | update_references_record | Updates all RecordReferences that refer to the updated object and reindexes all referring Records |
| after_record_delete    | delete_references_record | Deletes all RecordReferences referring to the deleted Record |

## Module API

You can access all the API functions this module exposes through the `current_oarepo_references` proxy.
*For more info, see [api.py](https://github.com/oarepo/oarepo-references/blob/master/oarepo_references/api.py)*.

## Tasks

An asynchronous (Celery) tasks could be launched in a group on all objects referring to a certain Record like this:

```python
from oarepo_references.utils import run_task_on_referrers

run_task_on_referrers(referred,
                      task.s(),
                      success_task.s(),
                      error_task.s())
```

Further documentation is available on
https://oarepo-references.readthedocs.io/
