Toolium Changelog
=================

v1.1.0
------

*In development*

- New MobilePageObject class to test Android and iOS apps with same base page object

v1.0.1
------

*Release date: 2016-05-09*

- Fix wait_until_first_element_is_found error when element is None
- Fix app_strings initialization in page objects
- Fix swipe method to work with Appium 1.5 swipe

v1.0.0
------

*Release date: 2016-04-12*

DRIVER

- Refactor to move config property 'browser' in [Browser] section to 'type' property in [Driver] section
- Allow to run API tests with behave: driver type property must be empty
- Refactor to rename 'driver_path' config properties to 'chrome_driver_path', 'explorer_driver_path',
  'edge_driver_path', 'opera_driver_path' and 'phantomjs_driver_path'
- Refactor to move config properties 'reuse_driver' and 'implicitly_wait' from [Common] section to [Driver] section
- Add a new config property 'appium_app_strings' in [Driver] section to request app strings before each Appium test
- Add new config properties 'window_width' and 'window_height' in [Driver] section to configure browser window size
- Upload the error screenshot to Jira if the test fails
- Allow to add extensions to firefox profile from properties file

   New config section [FirefoxExtensions] with extensions file paths, e.g. 'firebug = firebug-3.0.0-beta.3.xpi'

- Allow to use a predefined firefox profile

   New config property 'profile' in [Firefox] section to configure the profile directory

- Allow to set chrome arguments from properties file

   New config section [ChromeArguments] with chrome arguments, e.g. 'lang = es'

PAGE OBJECTS

- Save WebElement in PageElement to avoid searching the same element multiple times
- Refactor to rename get_element to get_web_element in Utils class and element to web_element in PageElement class
- Add *wait_until_first_element_is_found* method to Utils class to search a list of elements and wait until one of them
  is found
- Add new page element types: Checkbox, InputRadio, Link, Group and PageElements

BEHAVE

- Allow to modify Toolium properties from behave userdata configuration, e.g.:

.. code:: console

    $ behave -D Driver_type=chrome

VISUAL TESTING

- Refactor to rename assertScreenshot to assert_screenshot and assertFullScreenshot to assert_full_screenshot
- Add force parameter to *assert_screenshot* methods to compare the screenshot even if visual testing is disabled by
  configuration. If the assertion fails, the test fails.
- Baseline name property can contain *{PlatformVersion}* or *{RemoteNode}* to add actual platform version or remote
  node name to the baseline name


v0.12.1
-------

*Release date: 2016-01-07*

- Fix app_strings initialization in Behave Appium tests
- In Behave tests, Toolium config is saved in context.toolium_config instead of using context.config to avoid
  overriding Behave config

v0.12.0
-------

*Release date: 2015-12-23*

- Allow to create a second driver using DriverWrapper constructor:

.. code-block:: python

    second_wrapper = DriverWrapper()
    second_wrapper.connect()

- Fix page object issue with non-default driver. Now page object and utils init methods have both a driver_wrapper
  optional parameter instead of driver parameter.
- Fix swipe over an element in Android and iOS web tests
- Move set_config_* and set_output_* test case methods to ConfigFiles class
- Add behave environment file to initialize Toolium wrapper from behave tests

v0.11.3
-------

*Release date: 2015-11-24*

- Fix image size in visual testing for Android and iOS web tests
- Baseline name property allows any configuration property value to configure the visual testing baseline folder, e.g.:

   | {AppiumCapabilities_deviceName}-{AppiumCapabilities_platformVersion}: this baseline_name could use baselines as iPhone_6-8.3, iPhone_6-9.1, iPhone_6s-9.1, ...
   | {Browser_browser}: this baseline_name could use baselines as firefox, iexplore, ... (default value)

- Fix page elements initialization when they are defined outside of a page object

v0.11.2
-------

*Release date: 2015-11-11*

- Compatibility with Python 3

v0.11.1
-------

*Release date: 2015-11-02*

- New config property 'operadriver_path' in [Browser] section to configure the Opera Driver location
- Fix initialization error when a page object contains another page object
- Fix visual testing error if browser is phantomjs
- Fix firefox profile error in remote executions
- Configure setup.py to execute tests with 'python setup.py test'
- Convert markdown (.md) files to reStructuredText (.rst) and update long_description with README.rst content

v0.11.0
-------

*Release date: 2015-10-21*

- Rename library from seleniumtid to toolium
- Distributed under Apache Software License, Version 2

v0.10.0
-------

*Release date: 2015-09-23*

- Add support to Edge Windows browser
- New config property 'summary_prefix' in [Jira] section to modify default TCE summary
- Add scroll_element_into_view method to PageElement that scroll to element
- Add parent parameter to PageElement when element must be found from parent
- Page elements can be defined as class attributes, it is no longer necessary to define them as instance attributes in
  init_page_elements()
- Add wait_until_visible, wait_until_not_visible and assertScreenshot methods to PageElement
- Allow to set Chrome mobile options from properties file

   New config section [ChromeMobileEmulation] with mobile emulation options, e.g. 'deviceName = Google Nexus 5'

- Configuration system properties has been renamed

   | Old properties: Files_output_path, Files_log_filename, Files_properties, Files_logging
   | New properties: Output_directory, Output_log_filename, Config_directory, Config_prop_filenames, Config_log_filename

- Add set_config_* and set_output_* test case methods to configure output and config files instead of using
  configuration system properties

v0.9.3
------

*Release date: 2015-07-24*

- Allow to set custom driver capabilities from properties file

   New config section [Capabilities] with driver capabilities

- Fix set_value and app_strings errors in mobile web tests
- Fix set_value error in iOS tests when using needle

v0.9.2
------

*Release date: 2015-06-02*

- Allow to find elements by ios_uiautomation in visual assertions
- Fix app_strings error in mobile web tests
- Use set_value instead of send_keys to run tests faster

v0.9.1
------

*Release date: 2015-05-21*

- Add swipe method in Utils to allow swipe over an element
- Only one property file is mandatory if *Files_properties* has multiple values
- Allow to exclude elements from visual screenshots

v0.9.0
------

*Release date: 2015-05-12*

- Output path (screenshots, videos, visualtests) can be specified with a system property: *Files_output_path*
- Update app_strings in Appium tests only if the driver has changed
- Move visual properties from [Server] section to [VisualTests] section
- With a visual assertion error, the test can fail or give an error message and continue

   New config property 'fail' in [VisualTests] section to fail the test when there is a visual error

- Create a html report with the visual tests results

   New config property 'complete_report' in [VisualTests] section to include also correct visual assertions in report

- Configure multiple baseline name for different browsers, languages and versions

   | New config property 'baseline_name' in [VisualTests] section to configure the name of the baseline folder
   | Allow {browser}, {language} and {platformVersion} variables, e.g. baseline_name = {browser}-{language}
   | The default baseline_name is {browser}.

- Add assertFullScreenshot method in SeleniumTestCase

v0.8.6
------

*Release date: 2015-04-17*

- Add wait_until_element_visible method in utils class
- Logger filename can be specified with a system property: *Files_log_filename*

v0.8.5
------

*Release date: 2015-03-23*

- Add Button page element
- AppiumTestCase has a new attribute app_strings, a dict with application strings in the active language

v0.8.4
------

*Release date: 2015-03-05*

- Allow to set firefox and chrome preferences from properties file

   | New config section [FirefoxPreferences] with firefox preferences, e.g. 'browser.download.dir = /tmp'
   | New config section [ChromePreferences] with chrome preferences, e.g. 'download.default_directory = /tmp'

v0.8.3
------

*Release date: 2015-02-11*

- Read properties file before each test to allow executing tests with different configurations (android, iphone, ...)

v0.8.2
------

*Release date: 2015-02-04*

- Logging and properties config files can be specified with a system property: *Files_logging* and *Files_properties*

   *Files_properties* allows multiple files separated by ;

v0.8.1
------

*Release date: 2015-01-26*

- Fixed minor bugs
- Add visual testing to lettuce tests

v0.8
----

*Release date: 2015-01-20*

- Add visual testing to SeleniumTestCase and AppiumTestCase

   | New config property 'visualtests_enabled' in [Server] section to enable visual testing
   | New config property 'visualtests_save' in [Server] section to overwrite baseline images with actual screenshots
   | New config property 'visualtests_engine' in [Server] section to select image engine (pil or perceptualdiff)

v0.7
----

*Release date: 2014-12-23*

- Allow to autocomplete self.driver and self.utils in IDEs
- Remove non-mandatory requirements

v0.6
----

*Release date: 2014-12-05*

- Multiple tests of a class can be linked to the same Jira Test Case
- If test fails, the error message will be added as a comment to the Jira Test Case Execution
- Update Jira Test Cases also in lettuce tests

v0.5
----

*Release date: 2014-12-01*

- Downloads the saved video if the test has been executed in a VideoGrid
- Add BasicTestCase class to be used in Api tests or in other tests without selenium driver

v0.4
----

*Release date: 2014-11-12*

- Add Lettuce terrain file to initialize Selenium driver
- Add ConfigDriver.create_driver method to create a new driver with specific configuration
- Add wait_until_element_not_visible method in utils class

v0.3
----

*Release date: 2014-06-12*

- Add a config property 'implicitly_wait' in [Common] section to set an implicit timeout
- Add a config property 'reuse_driver' in [Common] section to use the same driver in all tests of each class
- The driver can be reused only in a test class setting a class variable 'reuse_driver = True'

v0.2
----

*Release date: 2014-05-13*

- Now depends on Appium 1.0

v0.1
----

*Release date: 2014-03-04*

- First version of the selenium library in python
