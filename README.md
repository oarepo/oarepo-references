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

## Mixins



## Signals

This module will register the following signal handlers on the Invenio Records signals that handle
managing of reference records whenever a Record changes:

| Invenio Records signal | Registered [signal handler](https://github.com/oarepo/oarepo-references/blob/master/oarepo_references/signals.py) | Description |
|------------------------|--------------------------|----------------------------------------------------------------------------------------------------------|
| after_record_insert    | create_references_record | Finds all references to other records in a Record and creates RecordReference entries for each reference |
| before_record_update   | convert_record_refs      | Transform Record data to contain references in an expected format (e.g any object with `links['self'] == url` is converted to `{'$ref': url}` |
| after_record_update    | update_references_record | Updates all RecordReferences that refer to the updated Record and reindexes all Records referring to the updated one |
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
