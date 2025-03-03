.. _driver_configuration:

Driver Configuration
====================

Toolium allows to run tests on web browsers (using Selenium or Playwright) or on mobile devices (using Appium). To
choose the browser or the mobile OS, configure :code:`type` property in :code:`[Driver]` section in
:code:`conf/properties.cfg` file with one of these values: :code:`firefox`, :code:`chrome`, :code:`iexplore`,
:code:`edge`, :code:`safari`, :code:`ios` or :code:`android`.

The following example shows how to choose Firefox::

    [Driver]
    type: firefox

If driver is not needed, typically in API tests, disable it using an empty string, :code:`api` or :code:`no_driver`::

    [Driver]
    type: api

By default, Toolium configuration is loaded from :code:`conf/properties.cfg` and :code:`conf/local-properties.cfg`
files. If different properties files are used for different environments, they can be selected using a system property
named :code:`TOOLIUM_CONFIG_ENVIRONMENT`. For example, if :code:`TOOLIUM_CONFIG_ENVIRONMENT` value is :code:`android`,
Toolium configuration will be loaded from :code:`conf/properties.cfg`, :code:`conf/android-properties.cfg` and
:code:`local-android-properties.cfg` files:

Nose2:

.. code:: console

    $ TOOLIUM_CONFIG_ENVIRONMENT=android python -m nose2 web/tests/test_web.py

Pytest:

.. code:: console

    $ TOOLIUM_CONFIG_ENVIRONMENT=android python -m pytest web_pytest/tests/test_web_pytest.py

Behave:

.. code:: console

    $ behave -D TOOLIUM_CONFIG_ENVIRONMENT=android

- :ref:`Driver Configuration Modification <driver_configuration_modification>`
- :ref:`Browser Configuration <browser_configuration>`
- :ref:`Mobile Configuration <mobile_configuration>`
- :ref:`Playwright Configuration <playwright_configuration>`
- :ref:`Remote Driver Configuration <remote_configuration>`
- :ref:`Multiple Simultaneous Drivers <multiple_drivers>`
- :ref:`Reuse Driver <reuse_driver>`

.. toctree::
   :hidden:

   Driver Configuration Modification <driver_configuration_modification.rst>
   Browser Configuration <browser_configuration.rst>
   Mobile Configuration <mobile_configuration.rst>
   Playwright Configuration <playwright_configuration.rst>
   Remote Driver Configuration <remote_configuration.rst>
   Multiple Simultaneous Drivers <multiple_drivers.rst>
   Reuse Driver <reuse_driver.rst>
