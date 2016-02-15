# -*- coding: utf-8 -*-
u"""
Copyright 2015 Telefónica Investigación y Desarrollo, S.A.U.
This file is part of Toolium.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
import sys
import unittest

from toolium.config_driver import get_error_message_from_exception
from toolium.config_files import ConfigFiles
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.jira import change_all_jira_status
from toolium.visual_test import VisualTest


class BasicTestCase(unittest.TestCase):
    """A class whose instances are api test cases."""
    config_files = ConfigFiles()
    driver_wrapper = None

    @classmethod
    def get_subclass_name(cls):
        return cls.__name__

    def get_method_name(self):
        # Split remove the test suffix added by ddt library
        return self._testMethodName.split('___')[0]

    def get_subclassmethod_name(self):
        return self.__class__.__name__ + "." + self.get_method_name()

    @classmethod
    def tearDownClass(cls):
        change_all_jira_status()

    def setUp(self):
        # Configure logger and properties
        if not isinstance(self, SeleniumTestCase):
            self.driver_wrapper = DriverWrappersPool.get_default_wrapper()
            self.driver_wrapper.configure(False, self.config_files)
        # Get config and logger instances
        self.config = self.driver_wrapper.config
        self.logger = logging.getLogger(__name__)
        self.logger.info("Running new test: {0}".format(self.get_subclassmethod_name()))

    def tearDown(self):
        # Get unit test exception
        py2_exception = sys.exc_info()[1]
        try:
            # Python 3.4+
            exception_info = self._outcome.errors[-1][1] if len(self._outcome.errors) > 0 else None
            exception = exception_info[1] if exception_info else None
        except AttributeError:
            try:
                # Python 3.3
                exceptions_list = self._outcomeForDoCleanups.failures + self._outcomeForDoCleanups.errors
                exception = exceptions_list[0][1] if exceptions_list else None
            except AttributeError:
                # Python 2.7
                exception = py2_exception

        if not exception:
            self._test_passed = True
            self.logger.info("The test '{0}' has passed".format(self.get_subclassmethod_name()))
        else:
            self._test_passed = False
            error_message = get_error_message_from_exception(exception)
            self.logger.error("The test '{0}' has failed: {1}".format(self.get_subclassmethod_name(), error_message))


class SeleniumTestCase(BasicTestCase):
    """A class whose instances are Selenium test cases.

    Attributes:
        driver: webdriver instance
        utils: test utils instance

    :type driver: selenium.webdriver.remote.webdriver.WebDriver
    :type utils: toolium.utils.Utils
    """
    driver = None
    utils = None

    @classmethod
    def tearDownClass(cls):
        # Call BasicTestCase tearDownClass
        super(SeleniumTestCase, cls).tearDownClass()

        # Stop driver
        if SeleniumTestCase.driver:
            DriverWrappersPool.close_drivers_and_download_videos(cls.get_subclass_name())
            SeleniumTestCase.driver = None

    def setUp(self):
        # Get default driver wrapper
        self.driver_wrapper = DriverWrappersPool.get_default_wrapper()
        if not SeleniumTestCase.driver:
            # Create driver
            self.driver_wrapper.configure(True, self.config_files)
            self.driver_wrapper.connect()
        SeleniumTestCase.driver = self.driver_wrapper.driver
        self.utils = self.driver_wrapper.utils

        # Get common configuration of reusing driver
        self.reuse_driver = self.driver_wrapper.config.getboolean_optional('Common', 'reuse_driver')
        # Set implicitly wait
        self.utils.set_implicit_wait()
        # Call BasicTestCase setUp
        super(SeleniumTestCase, self).setUp()

    def tearDown(self):
        # Call BasicTestCase tearDown
        super(SeleniumTestCase, self).tearDown()
        test_name = self.get_subclassmethod_name().replace('.', '_')

        # Capture screenshot on error
        if not self._test_passed:
            DriverWrappersPool.capture_screenshots(test_name)

        # Write Webdriver logs to files
        self.utils.save_all_webdriver_logs(self.get_subclassmethod_name())

        # Close browser and stop driver if it must not be reused
        DriverWrappersPool.close_drivers_and_download_videos(test_name, self._test_passed, self.reuse_driver)
        if not self.reuse_driver:
            SeleniumTestCase.driver = None

    def assert_screenshot(self, element_or_selector, filename, threshold=0, exclude_elements=[], driver_wrapper=None):
        """Assert that a screenshot of an element is the same as a screenshot on disk, within a given threshold.

        :param element_or_selector: either a CSS/XPATH selector as a string or a WebElement object.
                                    If None, a full screenshot is taken.
        :param filename: the filename for the screenshot, which will be appended with ``.png``
        :param threshold: the threshold for triggering a test failure
        :param exclude_elements: list of CSS/XPATH selectors as a string or WebElement objects that must be excluded
                                 from the assertion.
        :param driver_wrapper: driver wrapper instance
        """
        file_suffix = self.get_method_name()
        VisualTest(driver_wrapper).assert_screenshot(element_or_selector, filename, file_suffix, threshold,
                                                    exclude_elements)

    def assert_full_screenshot(self, filename, threshold=0, exclude_elements=[], driver_wrapper=None):
        """Assert that a driver screenshot is the same as a screenshot on disk, within a given threshold.

        :param filename: the filename for the screenshot, which will be appended with ``.png``
        :param threshold: the threshold for triggering a test failure
        :param exclude_elements: list of CSS/XPATH selectors as a string or WebElement objects that must be excluded
                                 from the assertion.
        :param driver_wrapper: driver wrapper instance
        """
        file_suffix = self.get_method_name()
        VisualTest(driver_wrapper).assert_screenshot(None, filename, file_suffix, threshold, exclude_elements)


class AppiumTestCase(SeleniumTestCase):
    """A class whose instances are Appium test cases.

    Attributes:
        app_strings: dict with application strings
    """
    app_strings = None

    @property
    def driver(self):
        """Get the Appium driver
         This method allows to autocomplete self.driver in IDEs

        :returns: Appium driver
        :rtype: appium.webdriver.webdriver.WebDriver
        """
        return super(AppiumTestCase, self).driver

    def setUp(self):
        super(AppiumTestCase, self).setUp()
        AppiumTestCase.app_strings = self.driver_wrapper.app_strings
