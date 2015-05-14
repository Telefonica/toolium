seleniumtid changelog
=====================

v0.9.1
------

*Release date: 2015-05-??*

  * Add swipe method in Utils to allow swipe over an element
  * Only one property file is mandatory if *Files_properties* has multiple values

v0.9.0
------

*Release date: 2015-05-12*

  * Output path (screenshots, videos, visualtests) can be specified with a system property: *Files_output_path*
  * Update app_strings in Appium tests only if the driver has changed
  * Move visual properties from [Server] section to [VisualTests] section
  * With a visual assertion error, the test can fail or give an error message and continue
    New config property 'fail' in [VisualTests] section to fail the test when there is a visual error
  * Create a html report with the visual tests results
    New config property 'complete_report' in [VisualTests] section to include also correct visual assertions in report
  * Configure multiple baseline name for different browsers, languages and versions
    New config property 'baseline_name' in [VisualTests] section to configure the name of the baseline folder
    Allow {browser}, {language} and {platformVersion} variables, i.e. baseline_name = {browser}-{language}. The default baseline_name is {browser}.
  * Add assertFullScreenshot method in SeleniumTestCase

v0.8.6
------

*Release date: 2015-04-17*

  * Add wait_until_element_visible method in utils class
  * Logger filename can be specified with a system property: *Files_log_filename*

v0.8.5
------

*Release date: 2015-03-23*

  * Add Button page element
  * AppiumTestCase has a new attribute app_strings, a dict with application strings in the active language

v0.8.4
------

*Release date: 2015-03-05*

  * Allow to set firefox and chrome preferences from properties file  
    New config section [FirefoxPreferences] with firefox preferences, e.g. 'browser.download.dir = /tmp'  
    New config section [ChromePreferences] with chrome preferences, e.g. 'download.default_directory = /tmp'

v0.8.3
------

*Release date: 2015-02-11*

  * Read properties file before each test to allow executing tests with different configurations (android, iphone, ...)

v0.8.2
------

*Release date: 2015-02-04*

  * Logging and properties config files can be specified with a system property: *Files_logging* and *Files_properties*  
    *Files_properties* allows multiple files separated by ;

v0.8.1
------

*Release date: 2015-01-26*

  * Fixed minor bugs
  * Add visual testing to lettuce tests

v0.8
----

*Release date: 2015-01-20*

  * Add visual testing to SeleniumTestCase and AppiumTestCase  
    New config property 'visualtests_enabled' in [Server] section to enable visual testing  
    New config property 'visualtests_save' in [Server] section to overwrite baseline images with actual screenshots  
    New config property 'visualtests_engine' in [Server] section to select image engine (pil or perceptualdiff)

v0.7
----

*Release date: 2014-12-23*

  * Allow to autocomplete self.driver and self.utils in IDEs
  * Remove non-mandatory requirements

v0.6
----

*Release date: 2014-12-05*

  * Multiple tests of a class can be linked to the same Jira Test Case
  * If test fails, the error message will be added as a comment to the Jira Test Case Execution
  * Update Jira Test Cases also in lettuce tests 

v0.5
----

*Release date: 2014-12-01*

  * Downloads the saved video if the test has been executed in a VideoGrid
  * Add BasicTestCase class to be used in Api tests or in other tests without selenium driver

v0.4
----

*Release date: 2014-11-12*

  * Add Lettuce terrain file to initialize Selenium driver
  * Add ConfigDriver.create_driver method to create a new driver with specific configuration
  * Add wait_until_element_not_visible method in utils class

v0.3
----

*Release date: 2014-06-12*

  * Add a config property 'implicitly_wait' in [Common] section to set an implicit timeout
  * Add a config property 'reuse_driver' in [Common] section to use the same driver in all tests of each class
  * The driver can be reused only in a test class setting a class variable 'reuse_driver = True'

v0.2
----

*Release date: 2014-05-13*

  * Now depends on Appium 1.0

v0.1
----

*Release date: 2014-03-04*

  * First version of the selenium library in python