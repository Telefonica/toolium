.. _driver_configuration_modification:

Driver Configuration Modification
=================================

Modify configuration by system properties
-----------------------------------------

Properties values configured by properties files can be overridden with system properties. To modify a particular option
within a section, a new system variable should be defined. The property name must be `TOOLIUM_[SECTION]_[OPTION]` and
its value must be `[Section]_[option]=value`, as can be seen in the following example:

.. code:: console

    $ export TOOLIUM_DRIVER_TYPE=Driver_type=chrome

This system property means the same as having the following section in the configuration file::

    [Driver]
    type: chrome

Underscore is allowed in options, but not in sections, for instance:

.. code:: console

    $ export TOOLIUM_SERVER_VIDEO_ENABLED=Server_video_enabled=true

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
            self.config.set('Capabilities', 'selenoid:options', "{'enableVideo': True}"):

    DriverWrapper.finalize_properties_configuration = finalize_properties_configuration
