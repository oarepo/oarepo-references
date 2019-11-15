# -*- coding: utf-8 -*-
"""OARepo record references utility functions."""

from __future__ import absolute_import, print_function


def transform_dicts_in_data(data, func):
    """
    Calls a function on all dicts contained in data input
    :param data: data dict or list
    """
    if isinstance(data, list):
        data = {'_': data}

    for key,value in data.items():
        if isinstance(value, dict):
            data[key] = transform_dicts_in_data(value, func)
        elif isinstance(value, list):
            for idx, v in enumerate(value):
                if isinstance(v, dict) or isinstance(v, list):
                    data[key][idx] = transform_dicts_in_data(v, func)
            continue

    if isinstance(data, dict):
        return func(data)


def keys_in_dict(data, key='$ref'):
    """
    Returns an array of all key occurences in a given dict
    :param record: data dict or list
    :return: Array[object] list of values of all occurences of a given key
    """
    if isinstance(data, list):
        data = {'_': data}

    for k, v in data.items():
        if k == key:
            yield v
        if isinstance(v, dict):
            for result in keys_in_dict(v, key):
                yield result
        elif isinstance(v, list):
            for d in v:
                if isinstance(d, dict) or isinstance(d, list):
                    for result in keys_in_dict(d, key):
                        yield result
