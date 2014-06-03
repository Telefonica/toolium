# -*- coding: utf-8 -*-
'''
(c) Copyright 2014 Telefonica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefonica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefonica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
'''
import unittest
import logging
import sys
import os
from selenium_tid_python import selenium_driver


class SeleniumTestCase(unittest.TestCase):
    driver = None
    reuse = False

    def get_subclassmethod_name(self):
        return self.__class__.__name__ + "." + self._testMethodName

    @classmethod
    def tearDownClass(cls):
        if SeleniumTestCase.driver != None:
            SeleniumTestCase.driver.quit()
            SeleniumTestCase.driver = None

    def setUp(self):
        # Configure logger
        self.logger = logging.getLogger(__name__)
        # Create driver
        if SeleniumTestCase.driver == None:
            SeleniumTestCase.driver = selenium_driver.connect()
        # Add implicitly wait
        config = selenium_driver.config
        implicitly_wait = config.get_optional('Common', 'implicitly_wait')
        if (implicitly_wait):
            SeleniumTestCase.driver.implicitly_wait(implicitly_wait)
        # Maximize browser
        if selenium_driver.is_maximizable():
            SeleniumTestCase.driver.maximize_window()
        self.logger.info("Running new test: {0}".format(self.get_subclassmethod_name()))

    def tearDown(self):
        # Check test result
        result = sys.exc_info()
        if result == (None, None, None):
            self.logger.info("The test '{0}' has passed".format(self.get_subclassmethod_name()))
        else:
            self.logger.error("The test '{0}' has failed: {1}".format(self.get_subclassmethod_name(), result[1]))
            # Capture screenshot
            test_name = self.get_subclassmethod_name().replace('.', '_')
            filename = '{0:0=2d}_{1}.png'.format(selenium_driver.screenshots_number, test_name)
            filepath = os.path.join(selenium_driver.screenshots_path, filename)
            if not os.path.exists(selenium_driver.screenshots_path):
                os.makedirs(selenium_driver.screenshots_path)
            if SeleniumTestCase.driver.get_screenshot_as_file(filepath):
                self.logger.error("Saved screenshot " + filepath)
                selenium_driver.screenshots_number += 1

        # Close browser and stop driver
        if not self.reuse:
            SeleniumTestCase.driver.quit()
            SeleniumTestCase.driver = None
