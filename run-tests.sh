#!/usr/bin/env sh
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

pydocstyle oarepo_references tests docs && \
isort -rc -c -df && \
check-manifest --ignore ".travis-*" && \
pytest
