# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records."""

from __future__ import absolute_import, print_function

import types
import typing
from marshmallow.fields import Nested


class ContextPassingNestedField(Nested):
    """Allows you to nest a :class:`Schema <marshmallow.Schema>` inside a field.

       This field also exposes validation context
       from a nested Schema to the parent schema.

       This is a workaround for:
       https://github.com/marshmallow-code/marshmallow/issues/1101
    """

    def _load(self, value, data, partial=None):
        valid_data = super(ContextPassingNestedField, self)._load(value, data, partial)
        return valid_data
