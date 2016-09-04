Installation
============

.. highlight:: console

HTTPolice is a Python package that requires Python 2.7 or 3.4+.
It can be installed like all other Python packages:
with `pip`__ from `PyPI`__.

__ https://pip.pypa.io/en/stable/
__ https://pypi.python.org/pypi/HTTPolice

If you’re not familiar with pip,
you may need to install it `manually`__ or `from your OS distribution`__.
You may also need development files and tools to compile dependencies.

__ https://pip.pypa.io/en/stable/installing/
__ https://packaging.python.org/en/latest/install_requirements_linux/

`PyPy`__ (the 2.7 variant) is also supported,
but you may experience problems with older PyPy versions (5.3.1 should be OK).

__ http://pypy.org/


On Debian/Ubuntu
----------------

::

  $ sudo apt-get install python-pip python-dev libxml2-dev libxslt1-dev zlib1g-dev libffi-dev

Then, to install the HTTPolice command-line tool into ``~/.local/bin``::

  $ pip install --user HTTPolice

Or, to install it system-wide::

  $ sudo pip install HTTPolice

Check that the installation was successful::

  $ httpolice --version
  HTTPolice 0.1.0


On Windows
----------
Unless you have a toolchain for building Python extensions,
you probably want to install a precompiled version of `lxml`__.
For example, at the time of writing,
`lxml 3.6.0`__ has precompiled packages for some versions of Python on Windows,
but `lxml 3.6.1`__ doesn't have any.
Therefore, you can `install Python 2.7`__ and ask for lxml 3.6.0::

  C:\>Python27\Scripts\pip install lxml==3.6.0

__ https://pypi.python.org/pypi/lxml
__ https://pypi.python.org/pypi/lxml/3.6.0
__ https://pypi.python.org/pypi/lxml/3.6.1
__ https://www.python.org/downloads/windows/

The same applies to `brotlipy`__.

__ https://pypi.python.org/pypi/brotlipy

Then you can install HTTPolice itself::

  C:\>Python27\Scripts\pip install HTTPolice

  C:\>Python27\Scripts\httpolice --version
  HTTPolice 0.1.0
