# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records."""
import typing

from marshmallow import missing, post_load


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

    @post_load
    def update_inline_changes(self, data, many, **kwargs):
        """Updates contents of the inlined reference."""
        changes = self.context.get('changed_reference', None)
        if changes and changes['url'] == self.ref_url(data):
            data = changes['content']

        return data

    @post_load
    def register_reference(self, data, many, **kwargs):
        """Registers reference to the validation context."""
        url = self.ref_url(data)
        self.register(url)
        return data


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
