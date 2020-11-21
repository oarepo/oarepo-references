# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records."""
import typing

import uuid

from flask import current_app
from flask_principal import Permission
from invenio_base.utils import obj_or_import_string
from invenio_pidstore import current_pidstore
from marshmallow import missing, post_load, pre_load


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


class InlineReferenceMixin(ReferenceFieldMixin):
    """Marshmallow mixin for inlined references."""

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


class CreateInlineReferenceMixin(InlineReferenceMixin):
    permission_factory = None
    object_serializer = None

    @pre_load
    def create_record_if_needed(self, data, many, **kwargs):
        already_created = False
        try:
            already_created = self.ref_url(data) is not None
        except KeyError:
            pass
        if already_created:
            return data

        # check if the caller can create the referenced record
        self.check_create_referenced_object_permissions(data)

        # create the referenced record
        created_object = self.create_referenced_object(data)

        # serialize the record to the final representation
        object_data = self.serialize_created_object(created_object)

        # hook for post processing the data if the extending schema wants to
        object_data = self.postprocess_created_object_data(object_data)

        # and return the serialized data
        return object_data

    def check_create_referenced_object_permissions(self, data):
        permission_factory = obj_or_import_string(self.permission_factory)
        if permission_factory:
            perm = permission_factory(data=data, schema=self)
            Permission(perm).require(http_exception=403)

    def create_referenced_object(self, data):
        raise RuntimeError('Implement "create_referenced_object" in your inline reference mixin')

    def serialize_created_object(self, created_object):
        object_serializer = obj_or_import_string(self.object_serializer)
        if object_serializer:
            object_data = object_serializer(created_object)
        else:
            object_data = dict(created_object)
        return object_data

    def postprocess_created_object_data(self, object_data):
        return object_data


class CreateInlineRecordReferenceMixin(CreateInlineReferenceMixin):
    pid_type = None

    def get_endpoint(self, test_func=lambda x: True):
        pid_type = self.pid_type
        # at first take default prefixes and then the rest
        for expected_default_endpoint_prefix in (True, False):
            for endpoint_name, endpoint in current_app.config['RECORDS_REST_ENDPOINTS'].items():
                endpoint_pid_type = endpoint.get('pid_type')
                if expected_default_endpoint_prefix != endpoint.get('default_endpoint_prefix', False):
                    continue
                if endpoint_pid_type == pid_type and test_func(endpoint):
                    return endpoint_name, endpoint
        return None, None

    def get_endpoint_prop(self, prop):
        if self.pid_type is None:
            raise NotImplementedError(f'Specify either "{prop}" or "pid_type" on class {type(self)}')
        endpoint_name, endpoint = self.get_endpoint(lambda x: x.get(prop))
        if not endpoint:
            raise AttributeError(f'Could not get {prop} for pid type {self.pid_type}')
        return endpoint[prop]

    @property
    def pid_minter(self):
        return self.get_endpoint_prop('pid_minter')

    @property
    def record_class(self):
        return self.get_endpoint_prop('record_class')

    def _resolve_minter(self, minter):
        if isinstance(minter, str):
            return current_pidstore.minters[minter]
        return minter

    def create_referenced_object(self, data):
        record_uuid = uuid.uuid4()
        minter = self._resolve_minter(self.pid_minter)
        minter(record_uuid, data)
        record_class = obj_or_import_string(self.record_class)
        created_record = record_class.create(data, id_=record_uuid)
        return created_record
