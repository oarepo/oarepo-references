# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records"""

from __future__ import absolute_import, print_function

from flask import current_app
from werkzeug.local import LocalProxy

current_oarepo_references = LocalProxy(
    lambda: current_app.extensions['oarepo-references'])
"""Helper proxy to access oarepo references state object."""
