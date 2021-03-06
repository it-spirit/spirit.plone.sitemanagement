# -*- coding: utf-8 -*-
"""Setup for spirit.plone.sitemanagement package."""

from setuptools import (
    find_packages,
    setup,
)

version = '0.4.dev0'
description = "Control your Plone sites from one management screen."
long_description = ('\n'.join([
    open('README.rst').read(),
    'Contributors',
    '------------\n',
    open('CONTRIBUTORS.rst').read(),
    open('CHANGES.rst').read(),
]))


install_requires = [
    'setuptools',
    # -*- Extra requirements: -*-
    'plone.api',
]

setup(
    name='spirit.plone.sitemanagement',
    version=version,
    description=description,
    long_description=long_description,
    # Get more strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.1",
        "Framework :: Plone :: 4.2",
        "Framework :: Plone :: 4.3",
        "Framework :: Plone :: 5.0",
        "Framework :: Plone :: 5.1",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
    ],
    keywords='plone zope management',
    author='it-spirit',
    author_email='thomas.massmann@it-spir.it',
    url='https://github.com/it-spirit/spirit.plone.sitemanagement',
    download_url='http://pypi.python.org/pypi/spirit.plone.sitemanagement',
    license='GPL version 2',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'': 'src'},
    namespace_packages=['spirit', 'spirit.plone'],
    include_package_data=True,
    zip_safe=False,
    extras_require=dict(
        test=[
            'plone.app.testing',
        ],
    ),
    install_requires=install_requires,
    entry_points="""
    # -*- Entry points: -*-

    [z3c.autoinclude.plugin]
    target = plone
    """,
)
