# -*- coding: utf-8 -*-
"""OARepo records references proxies."""

from flask import current_app
from werkzeug.local import LocalProxy

current_oarepo_references = LocalProxy(
    lambda: current_app.extensions['oarepo-references'])
"""Helper proxy to access flask taxonomies state object."""
