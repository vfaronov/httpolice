Installation
============

.. highlight:: console

HTTPolice is a Python package that requires Python 2.7 or 3.4+.
It can be installed like all other Python packages:
with `pip`__ from `PyPI`__.

__ https://pip.pypa.io/
__ https://pypi.python.org/pypi/HTTPolice

If you’re not familiar with pip,
you may need to install it `manually`__ or `from your OS distribution`__.
You may also need development files and tools to compile dependencies.

__ https://pip.pypa.io/page/installing/
__ https://packaging.python.org/guides/installing-using-linux-tools/

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
  HTTPolice 0.4.0


On Fedora
---------
Same as above, but use the following command to install dependencies::

  $ sudo dnf install python-pip gcc gcc-c++ redhat-rpm-config python-devel libxml2-devel libxslt-devel libffi-devel


On Windows
----------
HTTPolice uses libraries (`lxml`__ and `brotlipy`__) that include binary
CPython extensions. You probably want precompiled versions of these extensions,
and to get them, you may need specific versions of Python, lxml and brotlipy.

__ https://pypi.python.org/pypi/lxml
__ https://pypi.python.org/pypi/brotlipy

For example, at the time of writing, you can `install Python 3.6`__
and then simply do::

  C:\Users\Vasiliy\...\Python36>Scripts\pip install HTTPolice

Check that the installation was successful::

  C:\Users\Vasiliy\...\Python36>Scripts\httpolice --version
  HTTPolice 0.6.0

__ https://www.python.org/downloads/

However, it’s possible that new versions of lxml and brotlipy
might not have precompiled binaries for your version of Python,
and then you will have to check the `PyPI`__ pages of these libraries
to find a version that has suitable binaries (look for ``*-win32.whl``),
and install those specific versions **before** installing HTTPolice.
For example::

  C:\Users\Vasiliy\...\Python36>Scripts\pip install lxml==3.8.0
  C:\Users\Vasiliy\...\Python36>Scripts\pip install brotlipy==0.7.0

__ https://pypi.python.org/pypi
