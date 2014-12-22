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
from seleniumtid import selenium_driver
from seleniumtid.utils import Utils, classproperty
from seleniumtid.jira import change_all_jira_status
from seleniumtid.config_driver import get_error_message_from_exception


class BasicTestCase(unittest.TestCase):
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
    _driver = None
    _utils = None
    remote_video_node = None

    @classproperty
    @classmethod
    def driver(cls):
        '''
        This method allows to autocomplete self.driver in IDEs
        :rtype selenium.webdriver.remote.webdriver.WebDriver
        '''
        return cls._driver

    @classproperty
    @classmethod
    def utils(cls):
        '''
        This method allows to autocomplete self.utils in IDEs
        :rtype seleniumtid.utils.Utils
        '''
        return cls._utils

    @classmethod
    def tearDownClass(cls):
        # Call BasicTestCase tearDownClass
        super(SeleniumTestCase, cls).tearDownClass()

        # Stop driver
        if SeleniumTestCase._driver:
            class_name = cls.get_subclass_name()
            cls._finalize_driver(class_name)

    @classmethod
    def _finalize_driver(cls, video_name, test_passed=True):
        # Get session id to request the saved video
        session_id = cls._driver.session_id

        # Close browser and stop driver
        cls._driver.quit()
        cls._driver = None

        # Download saved video if video is enabled or if test fails
        if cls.remote_video_node and (selenium_driver.config.getboolean_optional('Server', 'video_enabled')
                                      or not test_passed):
            video_name = video_name if test_passed else 'error_{}'.format(video_name)
            cls._utils.download_remote_video(cls.remote_video_node, session_id, video_name)

    def setUp(self):
        # Create driver
        if not SeleniumTestCase._driver:
            SeleniumTestCase._driver = selenium_driver.connect()
            SeleniumTestCase._utils = Utils(SeleniumTestCase._driver)
            SeleniumTestCase.remote_video_node = SeleniumTestCase._utils.get_remote_video_node()

        # Get common configuration of reusing driver
        self.reuse_driver = selenium_driver.config.getboolean_optional('Common', 'reuse_driver')
        # Set implicitly wait
        self._utils.set_implicit_wait()
        # Maximize browser
        if selenium_driver.is_maximizable():
            SeleniumTestCase._driver.maximize_window()
        # Call BasicTestCase setUp
        super(SeleniumTestCase, self).setUp()

    def tearDown(self):
        # Call BasicTestCase tearDown
        super(SeleniumTestCase, self).tearDown()

        # Capture screenshot on error
        test_name = self.get_subclassmethod_name().replace('.', '_')
        if not self._test_passed:
            self._utils.capture_screenshot(test_name)

        # Stop driver
        if not self.reuse_driver:
            SeleniumTestCase._finalize_driver(test_name, self._test_passed)
