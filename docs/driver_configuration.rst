.. _driver_configuration:

Driver Configuration
====================

Toolium allows to run tests on web browsers (using Selenium) or on mobile devices (using Appium). To choose the browser
or the mobile OS, configure *browser* property in *[Browser]* section in properties.cfg file with one of these values:
firefox, chrome, iexplore, edge, safari, opera, phantomjs, ios or android.

The following example shows how to choose Firefox::

    [Browser]
    browser: firefox

- :ref:`Browser Configuration <browser_configuration>`
- :ref:`Mobile Configuration <mobile_configuration>`
- :ref:`Remote Driver Configuration <remote_configuration>`
- :ref:`Multiple Simultaneous Drivers <multiple_drivers>`

.. toctree::
   :hidden:

   Browser Configuration <browser_configuration.rst>
   Mobile Configuration <mobile_configuration.rst>
   Remote Driver Configuration <remote_configuration.rst>
   Multiple Simultaneous Drivers <multiple_drivers.rst>
