# -*- coding: utf-8 -*-
"""OARepo record references utility functions."""

from __future__ import absolute_import, print_function


def keys_in_dict(data: dict, key='$ref'):
    """
    Returns an array of all key occurences in a given dict
    :param record: data dict
    :return: Array[object] list of values of all occurences of a given key
    """
    for k, v in data.items():
        if k == key:
            yield v
        if isinstance(v, dict):
            for result in keys_in_dict(v, key):
                yield result
        elif isinstance(v, list):
            for d in v:
                for result in keys_in_dict(d, key):
                    yield result

