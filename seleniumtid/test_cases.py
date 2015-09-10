# -*- coding: utf-8 -*-

u"""
(c) Copyright 2014 Telefónica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefónica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefónica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
"""

import unittest
import logging
import sys

from seleniumtid import selenium_driver
from seleniumtid.utils import Utils
from seleniumtid.jira import change_all_jira_status
from seleniumtid.visual_test import VisualTest
from seleniumtid.config_driver import get_error_message_from_exception


class BasicTestCase(unittest.TestCase):
    """A class whose instances are api test cases."""
    _config_directory = None
    _output_directory = None
    _config_properties_filenames = None
    _config_log_filename = None
    _output_log_filename = None

    def set_config_directory(self, config_directory):
        """Set directory where configuration files are saved

        :param config_directory: configuration directory path
        """
        self._config_directory = config_directory

    def set_output_directory(self, output_directory):
        """Set output directory where log file and screenshots will be saved

        :param output_directory: output directory path
        """
        self._output_directory = output_directory

    def set_config_properties_filenames(self, *filenames):
        """Set properties files used to configure test cases

        :param filenames: list of properties filenames
        """
        self._config_properties_filenames = ';'.join(filenames)

    def set_config_log_filename(self, filename):
        """Set logging configuration file

        :param filename: logging configuration filename
        """
        self._config_log_filename = filename

    def set_output_log_filename(self, filename):
        """Set logging output file

        :param filename: logging configuration filename
        """
        self._output_log_filename = filename

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
            selenium_driver.configure(False, self._config_directory, self._output_directory,
                                      self._config_properties_filenames, self._config_log_filename,
                                      self._output_log_filename)
        # Configure logger
        self.logger = logging.getLogger(__name__)
        self.logger.info("Running new test: {0}".format(self.get_subclassmethod_name()))

    def tearDown(self):
        # Check test result
        result = sys.exc_info()[:2]
        if result == (None, None):
            self._test_passed = True
            self.logger.info("The test '{0}' has passed".format(self.get_subclassmethod_name()))
        else:
            self._test_passed = False
            error_message = get_error_message_from_exception(result[1])
            self.logger.error("The test '{0}' has failed: {1}".format(self.get_subclassmethod_name(), error_message))


class SeleniumTestCase(BasicTestCase):
    """A class whose instances are Selenium test cases.

    Attributes:
        driver: webdriver instance
        utils: test utils instance
        remote_video_node: hostname of the remote node if it has enabled a video recorder

    :type driver: selenium.webdriver.remote.webdriver.WebDriver
    :type utils: seleniumtid.utils.Utils
    """
    driver = None
    utils = None
    remote_video_node = None

    @classmethod
    def tearDownClass(cls):
        # Call BasicTestCase tearDownClass
        super(SeleniumTestCase, cls).tearDownClass()

        # Stop driver
        if SeleniumTestCase.driver:
            class_name = cls.get_subclass_name()
            cls._finalize_driver(class_name)

    @classmethod
    def _finalize_driver(cls, video_name, test_passed=True):
        # Get session id to request the saved video
        session_id = cls.driver.session_id

        # Close browser and stop driver
        cls.driver.quit()
        cls.driver = None
        SeleniumTestCase.driver = None

        # Download saved video if video is enabled or if test fails
        if cls.remote_video_node and (selenium_driver.config.getboolean_optional('Server', 'video_enabled')
                                      or not test_passed):
            video_name = video_name if test_passed else 'error_{}'.format(video_name)
            cls.utils.download_remote_video(cls.remote_video_node, session_id, video_name)

    def setUp(self):
        # Create driver
        if not SeleniumTestCase.driver:
            selenium_driver.configure(True, self._config_directory, self._output_directory,
                                      self._config_properties_filenames, self._config_log_filename,
                                      self._output_log_filename)
            SeleniumTestCase.driver = selenium_driver.connect()
            SeleniumTestCase.utils = Utils(SeleniumTestCase.driver)
            SeleniumTestCase.remote_video_node = SeleniumTestCase.utils.get_remote_video_node()
        # Get common configuration of reusing driver
        self.reuse_driver = selenium_driver.config.getboolean_optional('Common', 'reuse_driver')
        # Set implicitly wait
        self.utils.set_implicit_wait()
        # Maximize browser
        if selenium_driver.is_maximizable():
            SeleniumTestCase.driver.maximize_window()
        # Call BasicTestCase setUp
        super(SeleniumTestCase, self).setUp()

    def tearDown(self):
        # Call BasicTestCase tearDown
        super(SeleniumTestCase, self).tearDown()

        # Capture screenshot on error
        test_name = self.get_subclassmethod_name().replace('.', '_')
        if not self._test_passed:
            self.utils.capture_screenshot(test_name)

        # Stop driver
        if not self.reuse_driver:
            SeleniumTestCase._finalize_driver(test_name, self._test_passed)

    def assertScreenshot(self, element_or_selector, filename, threshold=0, exclude_elements=[]):
        """Assert that a screenshot of an element is the same as a screenshot on disk, within a given threshold.

        :param element_or_selector: either a CSS/XPATH selector as a string or a WebElement object.
                                    If None, a full screenshot is taken.
        :param filename: the filename for the screenshot, which will be appended with ``.png``
        :param threshold: the threshold for triggering a test failure
        :param exclude_elements: list of CSS/XPATH selectors as a string or WebElement objects that must be excluded
                                 from the assertion.
        """
        file_suffix = self.get_method_name()
        VisualTest().assertScreenshot(element_or_selector, filename, file_suffix, threshold, exclude_elements)

    def assertFullScreenshot(self, filename, threshold=0, exclude_elements=[]):
        """Assert that a driver screenshot is the same as a screenshot on disk, within a given threshold.

        :param filename: the filename for the screenshot, which will be appended with ``.png``
        :param threshold: the threshold for triggering a test failure
        :param exclude_elements: list of CSS/XPATH selectors as a string or WebElement objects that must be excluded
                                 from the assertion.
        """
        file_suffix = self.get_method_name()
        VisualTest().assertScreenshot(None, filename, file_suffix, threshold, exclude_elements)


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
        if AppiumTestCase.app_strings is None and not selenium_driver.is_web_test():
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
