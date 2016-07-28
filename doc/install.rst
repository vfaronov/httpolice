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
You may also need development files and tools for `lxml`__ dependencies.

__ https://pip.pypa.io/en/stable/installing/
__ https://packaging.python.org/en/latest/install_requirements_linux/
__ http://lxml.de/installation.html

`PyPy`__ (the 2.7 variant) is also supported,
but you may experience problems with older PyPy versions (5.3.1 should be OK).

__ http://pypy.org/


On Debian/Ubuntu
----------------

::

  $ sudo apt-get install python-dev libxml2-dev libxslt1-dev zlib1g-dev
  $ sudo apt-get install python-pip

Then, to install the HTTPolice command-line tool into ``~/.local/bin``::

  $ pip install --user HTTPolice

Or, to install it system-wide::

  $ sudo pip install HTTPolice

Check that the installation was successful::

  $ httpolice --version
  HTTPolice 0.1.0


On Windows
----------
After `installing Python 2.7`__, something like this should do the trick::

  C:\>Python27\Scripts\pip install HTTPolice

  C:\>Python27\Scripts\httpolice --version
  HTTPolice 0.1.0

__ https://www.python.org/downloads/windows/
