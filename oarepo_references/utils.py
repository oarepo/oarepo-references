# -*- coding: utf-8 -*-
"""OARepo record references utility functions."""

from __future__ import absolute_import, print_function

from urllib.parse import urlsplit

from flask import current_app
from invenio_records import Record
from invenio_records_rest.errors import PIDRESTException
from werkzeug.exceptions import NotFound

from oarepo_references.proxies import current_oarepo_references


def run_task_on_referrers(reference, task):
    """
    Iterates over all referrers referring the given reference and
    submits a celery task for each referrer.
    """
    refs = current_oarepo_references.get_records(reference)
    for ref in refs:
        rec = Record.get_record(id_=ref.record_uuid)
        task.delay(rec)


def transform_dicts_in_data(data, func):
    """
    Calls a function on all dicts contained in data input.

    :param func: transform func to apply on each dict in data
    :param data: data dict or list
    """

    def _transform_value(val, k):
        if isinstance(val, dict):
            data[k] = transform_dicts_in_data(val, func)
        elif isinstance(val, list):
            for idx, v in enumerate(val):
                if isinstance(v, dict) or isinstance(v, list):
                    data[k][idx] = transform_dicts_in_data(v, func)

    if isinstance(data, list):
        for idx, item in enumerate(data):
            _transform_value(item, idx)
        # TODO: find out why we need to wrap list in dict like this
        return {'_': data}

    for key, value in data.items():
        _transform_value(value, key)

    if isinstance(data, dict):
        return func(data)


def keys_in_dict(data, key='$ref', required_type=None):
    """
    Returns an array of all key occurrences in a given dict.

    :param data: haystack in which we are looking for needle
    :param key: a key name we should be looking for
    :param required_type: a required type of a value
    :return: Array[object] list of values of all occurrences of a given key.
    """
    if isinstance(data, list):
        data = {'_': data}

    for k, v in data.items():
        if k == key:
            if not required_type or isinstance(v, required_type):
                yield v
        if isinstance(v, dict):
            for result in keys_in_dict(v, key, required_type):
                yield result
        elif isinstance(v, list):
            for d in v:
                if isinstance(d, dict) or isinstance(d, list):
                    for result in keys_in_dict(d, key, required_type):
                        yield result


def get_reference_uuid(ref_url):
    """Returns a record uuid of the given reference or None if the referenced object could not be found."""
    if not isinstance(ref_url, str):
        return None

    if hasattr(current_app.wsgi_app, 'mounts') and current_app.wsgi_app.mounts:
        api_app = current_app.wsgi_app.mounts.get('/api', current_app)
    else:
        api_app = current_app

    parts = urlsplit(ref_url)

    if parts.netloc != api_app.config['SERVER_NAME']:
        # The referenced resource is not on our server
        return None

    matcher = api_app.url_map.bind(parts.netloc)

    try:
        if parts.path.startswith('/api'):
            loader, args = matcher.match(parts.path[4:])
        else:
            loader, args = matcher.match(parts.path)
    except NotFound:
        return None

    if 'pid_value' not in args:
        return None

    pid = args['pid_value']
    try:
        pid, record = pid.data
    except PIDRESTException:
        return None
    return pid.object_uuid
