.. _remote_configuration:

Remote Configuration
====================

Basic Configuration
-------------------

This section shows how to launch tests on a remote Selenium, Appium or GGR server. Configure its properties in *[Server]*
section in properties.cfg file::

    [Server]
    enabled: true
    ssl: false
    host: SERVER_IP
    port: SERVER_PORT
    username: SERVER_USERNAME
    password: SERVER_PASSWORD
    video_enabled: false
    logs_enabled: false
    log_types: all

enabled
~~~~~~~
| *true*: remote execution is enabled, tests will be executed remotely
| *false*: remote execution is disabled, tests will be executed locally

ssl
~~~
| *true*: use https in server url
| *false*: use http in server url

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
| This property is only valid using `Selenium Grid Extras <https://github.com/groupon/Selenium-Grid-Extras>`_ or
| `GGR with Selenoid <https://github.com/aerokube/ggr>`_ as remote server, that allow recording videos of test
| executions.
|
| *true*: remote video recording is enabled, a video of the test execution will be recorded and saved locally
| *false*: remote video recording is disabled

logs_enabled
~~~~~~~~~~~~
| *true*: webdriver and GGR logs are downloaded and saved to local files after test execution
| *false*: webdriver and GGR logs are downloaded and saved to local files only if the test fails

log_types
~~~~~~~~~~
| Comma-separated list of webdriver log types that will be downloaded if remote test fails or if *logs_enabled* is true
|
| *all*: all available log types in remote server will be downloaded (default value)
| '': setting an empty string, no log types will be downloaded
| *client,server*: in this example, only client and server logs will be downloaded


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
