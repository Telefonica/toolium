seleniumtid changelog
=====================

v0.8.1
------

*Release date: 2015-01-??*

  * Fixed minor bugs

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