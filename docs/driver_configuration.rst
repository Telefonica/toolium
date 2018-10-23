.. _driver_configuration:

Driver Configuration
====================

Toolium allows to run tests on web browsers (using Selenium) or on mobile devices (using Appium). To choose the browser
or the mobile OS, configure :code:`type` property in :code:`[Driver]` section in :code:`conf/properties.cfg` file with
one of these values: :code:`firefox`, :code:`chrome`, :code:`iexplore`, :code:`edge`, :code:`safari`, :code:`opera`,
:code:`phantomjs`, :code:`ios` or :code:`android`.

The following example shows how to choose Firefox::

    [Driver]
    type: firefox

If driver is not needed, typically in API tests, disable it using an empty string, :code:`api` or :code:`no_driver`::

    [Driver]
    type: api

By default, Toolium configuration is loaded from :code:`conf/properties.cfg` and :code:`conf/local-properties.cfg` files. If
different properties files are used for different environments, they can be selected using a system property named
:code:`Config_environment`. For example, if :code:`Config_environment` value is :code:`android`, Toolium configuration
will be loaded from :code:`conf/properties.cfg`, :code:`conf/android-properties.cfg` and
:code:`local-android-properties.cfg` files:

Nose:

.. code:: console

    $ Config_environment=android nosetests web/tests/test_web.py

Pytest:

.. code:: console

    $ Config_environment=android pytest web_pytest/tests/test_web_pytest.py

Behave:

.. code:: console

    $ behave -D Config_environment=android

- :ref:`Browser Configuration <browser_configuration>`
- :ref:`Mobile Configuration <mobile_configuration>`
- :ref:`Remote Driver Configuration <remote_configuration>`
- :ref:`Multiple Simultaneous Drivers <multiple_drivers>`
- :ref:`Reuse Driver <reuse_driver>`

.. toctree::
   :hidden:

   Browser Configuration <browser_configuration.rst>
   Mobile Configuration <mobile_configuration.rst>
   Remote Driver Configuration <remote_configuration.rst>
   Multiple Simultaneous Drivers <multiple_drivers.rst>
   Reuse Driver <reuse_driver.rst>
