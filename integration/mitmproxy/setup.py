# -*- coding: utf-8; -*-

import io
import os
import re

from setuptools import setup


with io.open(os.path.join('mitmproxy_httpolice.py')) as f:
    code = f.read()
    version = re.search(u"__version__ = '(.*)'", code).group(1)

with io.open('README.rst') as f:
    long_description = f.read()


setup(
    name='mitmproxy-HTTPolice',
    version=version,
    description='mitmproxy integration for HTTPolice',
    long_description=long_description,
    url='https://github.com/vfaronov/httpolice',
    author='Vasiliy Faronov',
    author_email='vfaronov@gmail.com',
    license='MIT',
    install_requires=[
        'mitmproxy >=0.15',
        'HTTPolice >=0.2.0',
    ],
    py_modules=['mitmproxy_httpolice'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Quality Assurance',
    ],
    keywords='HTTP message request response standards RFC lint check proxy',
)
