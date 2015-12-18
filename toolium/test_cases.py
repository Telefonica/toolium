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

from toolium import toolium_wrapper
from toolium.config_driver import get_error_message_from_exception
from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrappersPool
from toolium.jira import change_all_jira_status
from toolium.visual_test import VisualTest


class BasicTestCase(unittest.TestCase):
    """A class whose instances are api test cases."""
    config_files = ConfigFiles()

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
            toolium_wrapper.configure(False, self.config_files)
        # Get config and logger instances
        self.config = toolium_wrapper.config
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
            cls._finalize_driver(cls.get_subclass_name())

    @classmethod
    def _finalize_driver(cls, video_name, test_passed=True):
        DriverWrappersPool.close_drivers()
        cls.driver = None
        SeleniumTestCase.driver = None
        DriverWrappersPool.download_videos(video_name, test_passed)

    def setUp(self):
        # Create driver
        if not SeleniumTestCase.driver:
            toolium_wrapper.configure(True, self.config_files)
            SeleniumTestCase.driver = toolium_wrapper.connect()
            SeleniumTestCase.utils = toolium_wrapper.utils
        # Get common configuration of reusing driver
        self.reuse_driver = toolium_wrapper.config.getboolean_optional('Common', 'reuse_driver')
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

        # Stop driver
        if not self.reuse_driver:
            self._finalize_driver(test_name, self._test_passed)

    def assertScreenshot(self, element_or_selector, filename, threshold=0, exclude_elements=[], driver_wrapper=None):
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
        VisualTest(driver_wrapper).assertScreenshot(element_or_selector, filename, file_suffix, threshold,
                                                    exclude_elements)

    def assertFullScreenshot(self, filename, threshold=0, exclude_elements=[], driver_wrapper=None):
        """Assert that a driver screenshot is the same as a screenshot on disk, within a given threshold.

        :param filename: the filename for the screenshot, which will be appended with ``.png``
        :param threshold: the threshold for triggering a test failure
        :param exclude_elements: list of CSS/XPATH selectors as a string or WebElement objects that must be excluded
                                 from the assertion.
        :param driver_wrapper: driver wrapper instance
        """
        file_suffix = self.get_method_name()
        VisualTest(driver_wrapper).assertScreenshot(None, filename, file_suffix, threshold, exclude_elements)


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
        if AppiumTestCase.app_strings is None and not toolium_wrapper.is_web_test():
            AppiumTestCase.app_strings = self.driver.app_strings()

    def tearDown(self):
        # Call SeleniumTestCase tearDown
        super(AppiumTestCase, self).tearDown()

        # Remove app strings
        if not self.reuse_driver:
            AppiumTestCase.app_strings = None

    @classmethod
    def tearDownClass(cls):
        # Call SeleniumTestCase tearDownClass
        super(AppiumTestCase, cls).tearDownClass()

        # Remove app strings
        AppiumTestCase.app_strings = None
