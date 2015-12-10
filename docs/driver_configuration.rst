Driver Configuration
====================

Toolium allows to run tests on web browsers (using Selenium) or on mobile devices (using Appium). To choose the browser
or the mobile OS, configure *browser* property in *[Browser]* section in properties.cfg file with one of these values:
firefox, chrome, iexplore, edge, safari, opera, phantomjs, iphone or android.

The following example shows how to choose Firefox::

    [Browser]
    browser: firefox

- `Browser Cnfiguration <browser_configuration.html>`_
- `Mobile Configuration <mobile_configuration.html>`_
- `Remote Driver Configuration <remote_configuration.html>`_
- `Multiple Simultaneous Drivers <multiple_drivers.html>`_

.. toctree::
   :hidden:

   Browser Configuration <browser_configuration.rst>
   Mobile Configuration <mobile_configuration.rst>
   Remote Driver Configuration <remote_configuration.rst>
   Multiple Simultaneous Drivers <multiple_drivers.rst>
