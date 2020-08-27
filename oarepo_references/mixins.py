# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records."""
import typing

from marshmallow import missing

from oarepo_references.schemas.fields.reference import ReferenceFieldMixin


class ReferenceEnabledRecordMixin(object):
    """Record that contains inlined references to other records."""

    def update_inlined_ref(self, url, uuid, ref_obj):
        """Update inlined reference content in a record."""
        self.commit(changed_reference={
            'url': url,
            'uuid': uuid,
            'content': ref_obj
        })

    def update_ref(self, old_url, new_url):
        """Update reference URL to another object."""
        self.commit(renamed_reference={
            'old_url': old_url,
            'new_url': new_url
        })


class ReferenceByLinkFieldMixin(ReferenceFieldMixin):
    """Marshmallow field that contains reference by link."""

    def deserialize(self,
                    value: typing.Any,
                    attr: str = None,
                    data: typing.Mapping[str, typing.Any] = None,
                    **kwargs):
        """Deserialize ``value``.

        :param value: The value to deserialize.
        :param attr: The attribute/key in `data` to deserialize.
        :param data: The raw input data passed to `Schema.load`.
        :param kwargs: Field-specific keyword arguments.
        :raise ValidationError: If an invalid value is passed or if a required value
            is missing.
        """
        changes = self.context.get('renamed_reference', None)
        if changes and value == changes['old_url']:
            value = changes['new_url']

        output = super(ReferenceByLinkFieldMixin, self).deserialize(value, attr, data, **kwargs)
        if output is missing:
            return output
        print('REGISTERING REFERENCE TO: ', output)
        self.register(output, inline=False)
        return output
