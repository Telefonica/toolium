.. _remote_configuration:

Remote Configuration
====================

Basic Configuration
-------------------

This section shows how to launch tests on a remote Selenium or Appium server. Configure its properties in *[Server]*
section in properties.cfg file::

    [Server]
    enabled: true
    host: SERVER_IP
    port: SERVER_PORT
    username: SERVER_USERNAME
    password: SERVER_PASSWORD
    video_enabled: false
    logs_enabled: false

enabled
~~~~~~~
| *true*: remote execution is enabled, tests will be executed remotely
| *false*: remote execution is disabled, tests will be executed locally

host
~~~~
| Server ip or host name where Selenium Server, Appium Server or Selenium Grid is already started

port
~~~~
| Port number where server is listening

username
~~~~~~~~
| Username that is passed to Selenium Grid hub when it requires basic authentication, like in GGR

password
~~~~~~~~
| Password that is passed to Selenium Grid hub when it requires basic authentication, like in GGR

video_enabled
~~~~~~~~~~~~~
| This property is only valid using `Selenium Grid Extras <https://github.com/groupon/Selenium-Grid-Extras>`_ as
| remote server, that among other features allows recording videos of test executions.

| *true*: remote video recording is enabled, a video of the test execution will be recorded and saved locally
| *false*: remote video recording is disabled

logs_enabled
~~~~~~~~~~~~
| *true*: webdriver logs are downloaded and saved to local files after test execution
| *false*: webdriver logs are downloaded and saved to local files only if the test fails


Remote Driver Capabilities
--------------------------

To configure remote driver, create a *[Capabilities]* section in properties.cfg file and add every capability that
you want to configure with its value.

The following example requests to the Selenium Grid Hub a Windows environment with Internet Explorer 11::

    [Driver]
    type: iexplore

    [Capabilities]
    version: 11
    platform: WINDOWS

See https://github.com/SeleniumHQ/selenium/wiki/DesiredCapabilities for the complete Selenium capabilities list.
