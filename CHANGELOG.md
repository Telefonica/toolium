seleniumtid changelog
=====================

v0.5
----

*Release date: 2014-11-??*

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