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
:code:`TOOLIUM_CONFIG_ENVIRONMENT`. For example, if :code:`TOOLIUM_CONFIG_ENVIRONMENT` value is :code:`android`,
Toolium configuration will be loaded from :code:`conf/properties.cfg`, :code:`conf/android-properties.cfg` and
:code:`local-android-properties.cfg` files:

Nose:

.. code:: console

    $ TOOLIUM_CONFIG_ENVIRONMENT=android nosetests web/tests/test_web.py

Pytest:

.. code:: console

    $ TOOLIUM_CONFIG_ENVIRONMENT=android pytest web_pytest/tests/test_web_pytest.py

Behave:

.. code:: console

    $ behave -D TOOLIUM_CONFIG_ENVIRONMENT=android

Modify configuration by system properties
-----------------------------------------

Properties values configured by properties files can be overridden with system properties. To modify a particular option
within a section, a new system variable should be defined. The property name must be `TOOLIUM_[SECTION]_[OPTION]` and
its value must be `[Section]_[option]=value`, as can be seen in the following example:

.. code:: console

    $ TOOLIUM_DRIVER_TYPE=Driver_type=chrome

This system property means the same as having the following section in the configuration file::

    [Driver]
    type: chrome

Underscore is allowed in options, but not in sections, for instance:

.. code:: console

    $ TOOLIUM_SERVER_VIDEO_ENABLED=Server_video_enabled=true

This is the same as having the following section in the configuration file::

    [Server]
    video_enabled: true

To be cross-platform, section and option must be configured both in the property name and in the first token of the
value because they are case sensitive and, in Windows, system properties names are case insensitive.

Modify configuration programmatically
-------------------------------------

Properties values can also be modified programmatically before Toolium uses them to start the driver. There is a method
named `finalize_properties_configuration`, called after reading configuration files and before starting the driver, that
can be monkey patched to modify properties values, for instance:

.. code:: python

    from toolium.driver_wrapper import DriverWrapper

    def finalize_properties_configuration(self):
        if self.config.getboolean_optional('Server', 'enabled'):
            self.config.set('Capabilities', 'enableVideo', 'true'):

    DriverWrapper.finalize_properties_configuration = finalize_properties_configuration


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
