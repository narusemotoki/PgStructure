#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


setup(
    name='PgStructure',
    version='0.0.1',
    description='You can check the database structure of PostgreSQL',
    long_description='''
    You can check the database structure of PostgreSQL.
    ''',
    classifiers=[
        'Topic :: Database',
        'Environment :: Web Environment',
        'Framework :: Bottle',
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
    ],
    keywords=['postgresql',],
    author='Motoki Naruse',
    author_email='motoki@naru.se',
    url='http://github.com/narusemotoki/pgstructure',
    license='GPLv3',
    packages=['pgstructure'],
    entry_points={
        'console_scripts': ['pgstructure=pgstructure:pgstructure'],
    },
    zip_safe=False,
    install_requires=open('requirements.txt').read().splitlines(),
    package_data = {
        'pgstructure': [
            'templates/*.*',
        ]
    },
)
