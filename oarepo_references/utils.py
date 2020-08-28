# -*- coding: utf-8 -*-
"""OARepo record references utility functions."""

from __future__ import absolute_import, print_function

from urllib.parse import urlsplit

from celery import chain
from flask import current_app
from invenio_base.utils import obj_or_import_string
from invenio_records import Record
from invenio_records_rest.errors import PIDRESTException
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import NotFound

from oarepo_references.proxies import current_references


def class_import_string(o):
    """Returns a fully qualified import path of an object class."""
    return f'{o.__class__.__module__}.{o.__class__.__qualname__}'


def run_task_on_referrers(reference, task, success_task=None, error_task=None):
    """
    Queues a task for all referrers referring the given reference.

    :param reference: reference for which to run the tasks on referrers
    :param task: a celery signature
    :param success_task: a celery signature to handle success of task chain
    :param error_task: a celery signature to handle error of a certain task
    """
    refs = current_references.get_records(reference)

    task_list = []
    rec_list = []

    for ref in refs:
        rec = Record.get_record(id_=ref.record.record_uuid)
        # Add the referencing record to the task signature
        record_task = task.clone(kwargs={'record': rec})
        if error_task:
            record_error = error_task.clone(kwargs={'record': rec})
            record_task = record_task.on_error(record_error)

        task_list.append(record_task)
        rec_list.append(rec)

    job = chain(
        *task_list
    )
    if success_task:
        job_result = job.apply_async(link=success_task.clone(kwargs={'records': rec_list}))
    else:
        job_result = job.apply_async()
    return job_result


def get_record_object(rec_ref):
    """Fetches an instance of a Record from a certain reference record."""
    rec = rec_ref.record
    rec_cls = obj_or_import_string(rec.class_name.name, Record)
    try:
        return rec_cls.get_record(rec.record_uuid)
    except NoResultFound:
        return None


def get_reference_uuid(ref_url):
    """
    Returns a record uuid of the given reference.

    Or None if the referenced object could not be found.
    """
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
