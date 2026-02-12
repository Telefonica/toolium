Toolium
=======

|Build Status| |Coverage Status| |CodeClimate| |Documentation Status|

Toolium is a Python wrapper tool of Selenium, Playwright and Appium libraries to test web and mobile applications in a single
project. It provides a way of choosing and configuring the driver through a configuration file, implements a Page Object
pattern and includes a simple visual testing solution.

.. |Build Status| image:: https://github.com/Telefonica/toolium/workflows/build/badge.svg?branch=master
   :target: https://github.com/Telefonica/toolium/actions?query=branch%3Amaster
.. |Documentation Status| image:: https://readthedocs.org/projects/toolium/badge/?version=latest
   :target: http://toolium.readthedocs.org/en/latest
.. |Coverage Status| image:: https://coveralls.io/repos/Telefonica/toolium/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/Telefonica/toolium?branch=master
.. |CodeClimate| image:: https://api.codeclimate.com/v1/badges/3e5773b2e5272b546f8a/maintainability
   :target: https://codeclimate.com/github/Telefonica/toolium/maintainability

Getting Started
---------------

Run ``pip install toolium`` to install the latest version from `PyPi <https://pypi.org/project/toolium>`_. It's
highly recommended to use a virtualenv.

The main dependencies are:

- `Selenium <http://docs.seleniumhq.org/>`_: to test web applications in major browsers (Firefox, Chrome, Internet
  Explorer, Edge or Safari)
- `Playwright <https://playwright.dev/>`_: to test web applications in major browsers (Firefox, Chrome, Edge or Safari)
  as an alternative to Selenium (Beta integration in toolium)
- `Appium-Python-Client <https://github.com/appium/python-client>`_: to test mobile applications (native, hybrid or web)
  in Android or iOS devices/emulators.
- `requests <http://docs.python-requests.org>`_: to test APIs

You might need to adjust the Selenium and Appium-Python-Client versions in your project.
In that case, follow the `compatibility matrix <https://github.com/appium/python-client?tab=readme-ov-file#compatibility-matrix>`_

**Using toolium-template**

The easiest way to get started is to clone `toolium-template <https://github.com/Telefonica/toolium-template>`_
project, run the example test and add your own tests and configuration.

.. code:: console

    $ git clone git@github.com:Telefonica/toolium-template.git
    $ cd toolium-template
    $ pip install -r requirements.txt

Now, just follow the `toolium-template instructions <https://github.com/Telefonica/toolium-template#running-tests>`_ to
know how to start your testing project.

**Running toolium-examples**

You can also clone `toolium-examples <https://github.com/Telefonica/toolium-examples>`_ to get more examples about how
to use the library to test web, Android or iOS applications, in different scenarios.

.. code:: console

    $ git clone git@github.com:Telefonica/toolium-examples.git
    $ cd toolium-examples
    $ pip install -r requirements.txt

Now, just follow the `toolium-examples instructions <https://github.com/Telefonica/toolium-examples#running-tests>`_ to
run the test examples.

Contributing
------------

If you want to collaborate in Toolium development, feel free to `fork it <https://github.com/Telefonica/toolium>`_
and create a pull request.

Then clone the repository and install the dependencies in your virtualenv:

.. code:: console

    $ git clone git@github.com:<your_github_user>/toolium.git
    $ cd toolium
    $ pip install -r requirements.txt
    $ pip install -r requirements_dev.txt

Before submitting your changes, make sure the code follows the project's style by running Ruff:

.. code:: console

    $ ruff check --fix .    # Fix linting issues
    $ ruff format .         # Format code

Then run the unit tests:

.. code:: console

    $ python -m pytest

Finally, before accepting your contribution, we need you to sign our
`Contributor License Agreement <https://raw.githubusercontent.com/telefonicaid/Licensing/master/ContributionPolicy.txt>`_
and send it to ruben.gonzalezalonso@telefonica.com.

Main Features
-------------

- `Choosing a driver through a configuration file </docs/driver_configuration.rst>`_
- `Page Object pattern </docs/page_objects.rst>`_
- `BDD integration </docs/bdd_integration.rst>`_
- `Visual testing solution </docs/visual_testing.rst>`_
- `Tests result analysis </docs/tests_result_analysis.rst>`_

Documentation
-------------

Further information about features and fixes included in each release: `CHANGELOG </CHANGELOG.rst>`_.

Complete library reference and documentation are available at `ReadTheDocs <http://toolium.readthedocs.org>`_.
