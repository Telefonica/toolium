Toolium
=======

|Build Status| |Coverage Status| |Code Health| |Documentation Status|

Toolium is a Python wrapper tool of Selenium and Appium libraries to test web and mobile applications in a single
project. It provides a way of choosing and configuring the driver through a configuration file, implements a Page Object
pattern and includes a simple visual testing solution.

Getting Started
---------------

The requirements to install Toolium are `Python 2.7 <http://www.python.org>`_ and
`pip <https://pypi.python.org/pypi/pip>`_. If you use Python 2.7.9+, you don't need to install pip separately.

Run ``pip install toolium`` to install the latest version from `PyPi <https://pypi.python.org/pypi/toolium>`_. It's
highly recommendable to use a virtualenv.

The main dependencies are:

- `Selenium <http://docs.seleniumhq.org/>`_: to test web applications in major browsers (Firefox, Chrome, Internet
  Explorer, Edge, Safari, Opera)
- `Appium-Python-Client <https://github.com/appium/python-client>`_: to test mobile applications (native, hybrid or web)
  in Android or iOS devices/emulators.
- `requests <http://docs.python-requests.org>`_: to test APIs

The easiest way of getting started is to clone `toolium-template <https://github.com/Telefonica/toolium-template>`_
project, run the example test and add your own tests and configuration.

.. code:: console

    $ git clone git@github.com:Telefonica/toolium-template.git
    $ cd toolium-template
    $ pip install -r requirements.txt
    $ nosetests

You can also clone `toolium-examples <https://github.com/Telefonica/toolium-examples>`_ to get more examples about how
to use the library to test web, Android or iOS applications, in different scenarios.

.. code:: console

    $ git clone git@github.com:Telefonica/toolium-examples.git
    $ cd toolium-examples
    $ pip install -r requirements.txt
    $ nosetests

Library documentation could be found in `ReadTheDocs <http://toolium.readthedocs.org>`_ and release notes in
`CHANGELOG <http://toolium.readthedocs.org/en/latest/changelog.html>`_.

Contributing
------------

If you want to collaborate in Toolium development, feel free of `forking it <https://github.com/Telefonica/toolium>`_
and asking for a pull request.

Don't forget to run unit tests:

.. code:: console

    $ git clone git@github.com:*your_github_user*/toolium.git
    $ cd toolium
    $ python setup.py test

Main Features
-------------

- `Choosing driver through a configuration file <http://toolium.readthedocs.org/en/latest/browser_configuration.html>`_
- Page Object pattern
- Visual testing solution
- Make a screenshot in the happenning of an error

.. |Build Status| image:: https://travis-ci.org/Telefonica/toolium.svg?branch=master
   :target: https://travis-ci.org/Telefonica/toolium.svg
.. |Documentation Status| image:: https://readthedocs.org/projects/toolium/badge/?version=latest
   :target: http://toolium.readthedocs.org/en/latest/?badge=latest
.. |Coverage Status| image:: https://coveralls.io/repos/Telefonica/toolium/badge.svg?branch=feature%2Fdocs&service=github
   :target: https://coveralls.io/github/Telefonica/toolium?branch=feature%2Fdocs
.. |Code Health| image:: https://landscape.io/github/Telefonica/toolium/feature/docs/landscape.svg?style=flat
   :target: https://landscape.io/github/Telefonica/toolium/feature/docs
