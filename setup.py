# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Miroslav Bauer, CESNET.
#
# oarepo-references is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records"""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

OAREPO_VERSION = os.environ.get('OAREPO_VERSION', '3.1.1')

tests_require = [
]

extras_require = {
    'docs': [
        'Sphinx>=1.5.1',
    ],
    'tests': [
        'oarepo[tests]~={version}'.format(version=OAREPO_VERSION),
        'flask-taxonomies>=6.6.8'
    ],
    'tests-es7': [
        'oarepo[tests-es7]~={version}'.format(version=OAREPO_VERSION),
        'flask-taxonomies>=6.6.8'
    ],
}

setup_requires = [
    'pytest-runner>=3.0.0,<5',
]

install_requires = [
]

packages = find_packages()

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('oarepo_references', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='oarepo-references',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    license='MIT',
    author='Miroslav Bauer, CESNET',
    author_email='bauer@cesnet.cz',
    url='https://github.com/oarepo/oarepo-references',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_db.models': [
            'oarepo_references = oarepo_references.models',
        ],
        'invenio_db.alembic': [
            'oarepo_references = oarepo_references:alembic',
        ],
        'invenio_base.apps': [
            'oarepo_references = oarepo_references:OARepoReferences',
        ],
        'invenio_base.api_apps': [
            'oarepo_references = oarepo_references.ext:OARepoReferences',
        ],
        'flask.commands': [
            'references = oarepo_references.cli:references',
        ],
        'invenio_i18n.translations': [
            'messages = oarepo_references',
        ],
        # TODO: Edit these entry points to fit your needs.
        # 'invenio_access.actions': [],
        # 'invenio_admin.actions': [],
        # 'invenio_assets.bundles': [],
        # 'invenio_base.api_apps': [],
        # 'invenio_base.api_blueprints': [],
        # 'invenio_base.blueprints': [],
        # 'invenio_celery.tasks': [],
        # 'invenio_db.models': [],
        # 'invenio_pidstore.minters': [],
        # 'invenio_records.jsonresolver': [],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 4 - Beta',
    ],
)
