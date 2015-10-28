toolium changelog
=================

v0.11.1
-------

*Release date: 2015-11-??*

-  Fix initialization error when a page object contains another page object
-  Fix visual testing error if browser is phantomjs
-  Configure setup.py to execute tests with 'python setup.py test'
-  Convert markdown (.md) files to reStructuredText (.rst) and update long\_description with README.rst content

v0.11.0
-------

*Release date: 2015-10-21*

-  Rename library from seleniumtid to toolium
-  Distributed under Apache Software License, Version 2

v0.10.0
-------

*Release date: 2015-09-23*

-  Add support to Edge Windows browser
-  New config property 'summary\_prefix' in [Jira] section to modify
   default TCE summary
-  Add scroll\_element\_into\_view method to PageElement that scroll to
   element
-  Add parent parameter to PageElement when element must be found from
   parent
-  Page elements can be defined as class attributes, it is no longer
   necessary to define them as instance attributes in
   init\_page\_elements()
-  Add wait\_until\_visible, wait\_until\_not\_visible and
   assertScreenshot methods to PageElement
-  Allow to set Chrome mobile options from properties file
   New config section [ChromeMobileEmulation] with mobile emulation
   options, e.g. 'deviceName = Google Nexus 5'
-  Configuration system properties has been renamed
   Old properties: Files\_output\_path, Files\_log\_filename,
   Files\_properties, Files\_logging,
   New properties: Output\_directory, Output\_log\_filename,
   Config\_directory, Config\_prop\_filenames, Config\_log\_filename
-  Add set\_config\_\* and set\_output\_\* test case methods to
   configure output and config files instead of using configuration
   system properties

v0.9.3
------

*Release date: 2015-07-24*

-  Allow to set custom driver capabilities from properties file New
   config section [Capabilities] with driver capabilities
-  Fix set\_value and app\_strings errors in mobile web tests
-  Fix set\_value error in iOS tests when using needle

v0.9.2
------

*Release date: 2015-06-02*

-  Allow to find elements by ios\_uiautomation in visual assertions
-  Fix app\_strings error in mobile web tests
-  Use set\_value instead of send\_keys to run tests faster

v0.9.1
------

*Release date: 2015-05-21*

-  Add swipe method in Utils to allow swipe over an element
-  Only one property file is mandatory if *Files\_properties* has
   multiple values
-  Allow to exclude elements from visual screenshots

v0.9.0
------

*Release date: 2015-05-12*

-  Output path (screenshots, videos, visualtests) can be specified with
   a system property: *Files\_output\_path*
-  Update app\_strings in Appium tests only if the driver has changed
-  Move visual properties from [Server] section to [VisualTests] section
-  With a visual assertion error, the test can fail or give an error
   message and continue New config property 'fail' in [VisualTests]
   section to fail the test when there is a visual error
-  Create a html report with the visual tests results New config
   property 'complete\_report' in [VisualTests] section to include also
   correct visual assertions in report
-  Configure multiple baseline name for different browsers, languages
   and versions New config property 'baseline\_name' in [VisualTests]
   section to configure the name of the baseline folder Allow {browser},
   {language} and {platformVersion} variables, i.e. baseline\_name =
   {browser}-{language}. The default baseline\_name is {browser}.
-  Add assertFullScreenshot method in SeleniumTestCase

v0.8.6
------

*Release date: 2015-04-17*

-  Add wait\_until\_element\_visible method in utils class
-  Logger filename can be specified with a system property:
   *Files\_log\_filename*

v0.8.5
------

*Release date: 2015-03-23*

-  Add Button page element
-  AppiumTestCase has a new attribute app\_strings, a dict with
   application strings in the active language

v0.8.4
------

*Release date: 2015-03-05*

-  Allow to set firefox and chrome preferences from properties file
   New config section [FirefoxPreferences] with firefox preferences,
   e.g. 'browser.download.dir = /tmp'
   New config section [ChromePreferences] with chrome preferences, e.g.
   'download.default\_directory = /tmp'

v0.8.3
------

*Release date: 2015-02-11*

-  Read properties file before each test to allow executing tests with
   different configurations (android, iphone, ...)

v0.8.2
------

*Release date: 2015-02-04*

-  Logging and properties config files can be specified with a system
   property: *Files\_logging* and *Files\_properties*
   *Files\_properties* allows multiple files separated by ;

v0.8.1
------

*Release date: 2015-01-26*

-  Fixed minor bugs
-  Add visual testing to lettuce tests

v0.8
----

*Release date: 2015-01-20*

-  Add visual testing to SeleniumTestCase and AppiumTestCase
   New config property 'visualtests\_enabled' in [Server] section to
   enable visual testing
   New config property 'visualtests\_save' in [Server] section to
   overwrite baseline images with actual screenshots
   New config property 'visualtests\_engine' in [Server] section to
   select image engine (pil or perceptualdiff)

v0.7
----

*Release date: 2014-12-23*

-  Allow to autocomplete self.driver and self.utils in IDEs
-  Remove non-mandatory requirements

v0.6
----

*Release date: 2014-12-05*

-  Multiple tests of a class can be linked to the same Jira Test Case
-  If test fails, the error message will be added as a comment to the
   Jira Test Case Execution
-  Update Jira Test Cases also in lettuce tests

v0.5
----

*Release date: 2014-12-01*

-  Downloads the saved video if the test has been executed in a
   VideoGrid
-  Add BasicTestCase class to be used in Api tests or in other tests
   without selenium driver

v0.4
----

*Release date: 2014-11-12*

-  Add Lettuce terrain file to initialize Selenium driver
-  Add ConfigDriver.create\_driver method to create a new driver with
   specific configuration
-  Add wait\_until\_element\_not\_visible method in utils class

v0.3
----

*Release date: 2014-06-12*

-  Add a config property 'implicitly\_wait' in [Common] section to set
   an implicit timeout
-  Add a config property 'reuse\_driver' in [Common] section to use the
   same driver in all tests of each class
-  The driver can be reused only in a test class setting a class
   variable 'reuse\_driver = True'

v0.2
----

*Release date: 2014-05-13*

-  Now depends on Appium 1.0

v0.1
----

*Release date: 2014-03-04*

-  First version of the selenium library in python
