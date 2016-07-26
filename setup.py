# -*- coding: utf-8; -*-

import io
import os

from setuptools import setup


metadata = {}
with io.open(os.path.join('httpolice', '__metadata__.py'), 'rb') as f:
    exec(f.read(), metadata)            # pylint: disable=exec-used

with io.open('README.rst') as f:
    long_description = f.read()

with io.open('requirements.in') as f:
    install_requires = [line for line in f
                        if line and not line.startswith('#')]


setup(
    name='HTTPolice',
    version=metadata['version'],
    description='Lint for HTTP',
    long_description=long_description,
    url='https://github.com/vfaronov/httpolice',
    author='Vasiliy Faronov',
    author_email='vfaronov@gmail.com',
    license='MIT',
    install_requires=install_requires,
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
        'License :: OSI Approved :: MIT License',
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
