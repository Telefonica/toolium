.. _tests_result_analysis:

Tests Result Analysis
=====================

Toolium does not create a custom tests execution report. This is delegated to your favourite test framework (unittest,
nose, pytest, behave, ...). But Toolium provides some useful features to analyze tests results.

Logs
----

Toolium internal logs are written in *output/toolium.log*. Your tests logs can be also written in the same file using
the already existing logger instance:

.. code-block:: python

    [TestCase or PageObject]
    self.logger.debug(message)

    [Behave steps]
    context.logger.debug(message)

Screenshots
-----------

Toolium makes a screenshot when a test fails and saves it into the folder *output/screenshots/DATE_DRIVER_TYPE*.

Besides, it's possible to make a screnshot at any time during the test and it will be saved into the same folder:

.. code-block:: python

    [TestCase or PageObject]
    self.utils.capture_screenshot(screenshot_name)

    [Behave steps]
    context.utils.capture_screenshot(screenshot_name)

Videos
------

When a test fails, Toolium downloads a video of the test execution into the folder *output/videos/DATE_DRIVER_TYPE*.
This feature only works when the test has been executed in a
`Selenium Grid Extras <https://github.com/groupon/Selenium-Grid-Extras>`_ or `GGR <https://github.com/aerokube/ggr>`_
grid node and the video recording has been enabled in grid. Both grids allow recording videos of test executions.

For example, to enable video recording in GGR, the following capability must be configured ::

    [Capabilities]
    selenoid___options: {'enableVideo': True}

In order to download the execution video even if the test passes, configure the property *video_enabled* in *[Server]*
section in properties.cfg file ::

    [Server]
    video_enabled: true

Webdriver logs
--------------

When a test fails during a remote execution, Toolium downloads webdriver logs into the folder *output*. Depending on
the driver type, the webdriver will contain different log types, for instance, *client*, *server*, *browser*, *driver*,
*performance*, *profiler*, *logcat*, *bugreport*, etc.

By default, when a test fails, toolium will download all log types available in current webdriver. But it can be also
configured to download only a set of log types setting the property
`log_types <https://toolium.readthedocs.io/en/latest/remote_configuration.html#log-types>`_ in *[Server]* section in
properties.cfg file ::

    [Server]
    log_types: client,server

Notice that if using Chrome, log types can be enabled in *[Capabilities]* section and performance log can be configured
in *[Chrome]* section::

    [Capabilities]
    goog___loggingPrefs: {'browser':'ALL', 'driver': 'ALL', 'performance': 'ALL'}

    [Chrome]
    options: {'perfLoggingPrefs': {'enableNetwork': True}}

Also take into account that, to enable logs in GGR, the following capability must be configured in *[Capabilities]*
section ::

    [Capabilities]
    selenoid___options: {'enableLog': True}

In order to download webdriver logs even if the test passes, configure the property
`logs_enabled <https://toolium.readthedocs.io/en/latest/remote_configuration.html#logs-enabled>`_ in *[Server]* section
in properties.cfg file ::

    [Server]
    logs_enabled: true
