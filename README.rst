Toolium
=======

| *toolium* is a wrapper tool for testing APIs, web and mobile
  applications using requests, selenium and appium libraries
| |Build Status| |Coverage Status| |Code Health| |Documentation Status|

Requirements
------------

Python 2.7 (http://www.python.org)

Installation
------------

Configure a virtual environment and install toolium package:

::

    virtualenv ENV
    source ENV/bin/activate
    pip install toolium

The following dependencies will be installed:

- requests (http://docs.python-requests.org)
- selenium (http://docs.seleniumhq.org/)
- Appium-Python-Client (https://github.com/appium/python-client)

Development installation
------------------------

Configure a virtual environment with the required packages:

::

    virtualenv ENV
    source ENV/bin/activate
    pip install -r requirements.txt
    pip install -r requirements_dev.txt

Documentation
-------------

See toolium docs in http://toolium.readthedocs.org

Release notes: `CHANGELOG.rst </CHANGELOG.rst>`__

.. |Build Status| image:: https://travis-ci.org/Telefonica/toolium.svg?branch=master
   :target: https://travis-ci.org/Telefonica/toolium.svg
.. |Documentation Status| image:: https://readthedocs.org/projects/toolium/badge/?version=latest
   :target: http://toolium.readthedocs.org/en/latest/?badge=latest
.. |Coverage Status| image:: https://coveralls.io/repos/Telefonica/toolium/badge.svg?branch=feature%2Fdocs&service=github
   :target: https://coveralls.io/github/Telefonica/toolium?branch=feature%2Fdocs
.. |Code Health| image:: https://landscape.io/github/Telefonica/toolium/feature/docs/landscape.svg?style=flat
   :target: https://landscape.io/github/Telefonica/toolium/feature/docs
