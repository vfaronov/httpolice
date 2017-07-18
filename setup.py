# -*- coding: utf-8; -*-

import io
import os
import re

from setuptools import setup


metadata = {}
with io.open(os.path.join('httpolice', '__metadata__.py'), 'rb') as f:
    exec(f.read(), metadata)            # pylint: disable=exec-used

with io.open('README.rst') as f:
    long_description = f.read()

# I prefer not to have shields in my package description. Shields reflect
# current status; they are good in a README when viewed on Git master,
# but not in versions published on PyPI.
long_description = re.sub(r'^\.\. status:.*?\n\n', u'', long_description,
                          flags=re.DOTALL | re.MULTILINE)

setup(
    name='HTTPolice',
    version=metadata['version'],
    description='Validator for HTTP',
    long_description=long_description,
    url=metadata['homepage'],
    author='Vasiliy Faronov',
    author_email='vfaronov@gmail.com',
    license='MIT',

    # NB: when updating these fields,
    # make sure you don't break ``tools/minimum_requires.sh``.
    install_requires=[
        'singledispatch >= 3.4.0.3',
        'six >= 1.10.0',
        'lxml >= 3.6.0',
        'bitstring >= 3.1.4',
        'dominate >= 2.2.0',
        'defusedxml >= 0.5.0',
        'brotlipy >= 0.5.1',
    ],
    extras_require={
        ':python_version == "2.7"': [
            'enum34 >= 1.1.6',
        ],
    },

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
        'httpolice.known': ['*.csv'],
        'httpolice.reports': ['html.css', 'html.js'],
    },
    entry_points={
        'console_scripts': [
            'httpolice=httpolice.cli:main',
        ],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Quality Assurance',
    ],
    keywords='HTTP message request response standards RFC lint validator',
)
