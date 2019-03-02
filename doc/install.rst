Installation
============

.. highlight:: console

HTTPolice is a Python package that requires `Python`__ 3.4+.
`PyPy`__ is also supported.

__ https://www.python.org/
__ http://pypy.org/

Like other Python packages, HTTPolice is installed with `pip`__ from `PyPI`__.
If you’re not familiar with pip,
you may need to install it `manually`__ or `from your OS distribution`__.

__ https://pip.pypa.io/
__ https://pypi.org/project/HTTPolice/
__ https://pip.pypa.io/page/installing/
__ https://packaging.python.org/guides/installing-using-linux-tools/


On Debian/Ubuntu
----------------

Depending on your setup, you may or may not need to install these packages::

  $ sudo apt-get install python3-pip python3-dev libxml2-dev libxslt1-dev zlib1g-dev

Then, to install the HTTPolice command-line tool into ``~/.local/bin``::

  $ pip3 install --user HTTPolice

Or, to install it system-wide::

  $ sudo pip3 install HTTPolice

Check that the installation was successful::

  $ httpolice --version
  HTTPolice 0.7.0


On Fedora
---------
Same as above, but the dependency packages are::

  $ sudo dnf install python3-pip gcc gcc-c++ redhat-rpm-config python3-devel libxml2-devel libxslt-devel


On Windows
----------
After installing `a recent Python`__, typically all you need to do is::

  C:\Users\Vasiliy\...\Python36>Scripts\pip install HTTPolice

Check that the installation was successful::

  C:\Users\Vasiliy\...\Python36>Scripts\httpolice --version
  HTTPolice 0.7.0

__ https://www.python.org/downloads/

But if ``pip install`` starts trying (and failing) to compile some libraries,
you may need to give it a hand: check the `PyPI`__ pages for those libraries
(such as `lxml`__ or `Brotli`__) to find versions that have suitable
pre-built binares (``*-win32.whl``), and install those specific versions first.
For example::

  C:\Users\Vasiliy\...\Python36>Scripts\pip install lxml==3.8.0
  C:\Users\Vasiliy\...\Python36>Scripts\pip install Brotli==1.0.4
  C:\Users\Vasiliy\...\Python36>Scripts\pip install HTTPolice

__ https://pypi.org/
__ https://pypi.org/project/lxml/
__ https://pypi.org/project/Brotli/
