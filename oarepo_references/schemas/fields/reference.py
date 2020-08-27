# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records."""


class ReferenceFieldMixin(object):
    """Field Mixin representing a reference to another object."""

    def register(self, reference, reference_uuid=None, inline=True):
        """Registers a reference to the validation context."""
        refspec = dict(
            reference=reference,
            reference_uuid=reference_uuid,
            inline=inline
        )
        try:
            self.context['references'].append(refspec)
        except KeyError:
            self.context['references'] = [refspec]
