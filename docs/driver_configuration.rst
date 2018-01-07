.. _driver_configuration:

Driver Configuration
====================

Toolium allows to run tests on web browsers (using Selenium) or on mobile devices (using Appium). To choose the browser
or the mobile OS, configure *type* property in *[Driver]* section in properties.cfg file with one of these values:
firefox, chrome, iexplore, edge, safari, opera, phantomjs, ios or android.

The following example shows how to choose Firefox::

    [Driver]
    type: firefox

By default, Toolium configuration is loaded from properties.cfg and local-properties.cfg files. If different properties
files are used for different environments, they can be selected using a system property named *Config_environment*. For
example, if *Config_environment* value is *android*, Toolium configuration will be loaded from properties.cfg,
android-properties.cfg and local-android-properties.cfg files:

.. code:: console

    $ Config_environment=android nosetests web/tests/test_web.py

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
