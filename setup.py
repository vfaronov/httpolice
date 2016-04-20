# -*- coding: utf-8; -*-

import io
import os

from setuptools import setup


metadata = {}
with io.open(os.path.join('httpolice', '__metadata__.py'), 'rb') as f:
    exec(f.read(), metadata)

with io.open('README.rst') as f:
    long_description = f.read()


setup(
    name='HTTPolice',
    version=metadata['version'],
    description='Lint for HTTP requests and responses',
    long_description=long_description,
    author='Vasiliy Faronov',
    author_email='vfaronov@gmail.com',
    install_requires=[
        'setuptools',
        'six >=1.10.0',
        'lxml >=3.6.0',
        'bitstring >=3.1.4',
        'dominate >=2.1.17',
        'defusedxml >=0.4.1',
    ],
    packages=[
        'httpolice',
        'httpolice.inputs',
        'httpolice.known',
        'httpolice.reports',
        'httpolice.syntax',
        'httpolice.util',
    ],
    package_data={
        'httpolice': ['notices.xml'],
        'httpolice.reports': ['html.css', 'html.js'],
    },
    entry_points={
        'console_scripts': [
            'httpolice=httpolice.cli:main',
        ],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Quality Assurance',
    ],
    keywords='HTTP message request response standards RFC lint check',
)