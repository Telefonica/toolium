# -*- coding: utf-8 -*-

u"""
(c) Copyright 2015 Telefónica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefónica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefónica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
"""

import unittest
import logging
import os

from seleniumtid.selenium_wrapper import SeleniumWrapper
from ddt import ddt, data, unpack
import mock


class SeleniumWrapperCommon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_path = os.path.dirname(os.path.realpath(__file__))

    def tearDown(self):
        # Remove environment properties
        try:
            del os.environ["Files_logging"]
            del os.environ["Files_properties"]
            del os.environ["Browser_browser"]
        except KeyError:
            pass
        # Remove previous wrapper instance
        SeleniumWrapper._instance = None


class SeleniumWrapperPropertiesTests(SeleniumWrapperCommon):
    def setUp(self):
        os.environ["Files_logging"] = os.path.join(self.root_path, 'conf', 'logging.conf')
        self.wrapper = SeleniumWrapper()
        self.wrapper.configure_logger()

    def test_configure_properties(self):
        os.environ["Files_properties"] = os.path.join(self.root_path, 'conf', 'properties.cfg')
        self.wrapper.configure_properties()
        self.assertEquals('firefox', self.wrapper.config.get('Browser', 'browser'))  # get last value
        self.assertEquals('5', self.wrapper.config.get_optional('Common', 'implicitly_wait'))  # only in properties
        self.assertEquals(None, self.wrapper.config.get_optional('AppiumCapabilities', 'app'))  # only in android

    def test_configure_properties_android(self):
        os.environ["Files_properties"] = os.path.join(self.root_path, 'conf', 'android-properties.cfg')
        self.wrapper.configure_properties()
        self.assertEquals('android', self.wrapper.config.get('Browser', 'browser'))  # get last value
        self.assertEquals(None, self.wrapper.config.get_optional('Common', 'implicitly_wait'))  # only in properties
        self.assertEquals('http://qacore02/sites/seleniumExamples/ApiDemos-debug.apk',
                          self.wrapper.config.get_optional('AppiumCapabilities', 'app'))  # only in android

    def test_configure_properties_two_files(self):
        os.environ["Files_properties"] = (os.path.join(self.root_path, 'conf', 'properties.cfg') + ';' +
                                          os.path.join(self.root_path, 'conf', 'android-properties.cfg'))
        self.wrapper.configure_properties()
        self.assertEquals('android', self.wrapper.config.get('Browser', 'browser'))  # get last value
        self.assertEquals('5', self.wrapper.config.get_optional('Common', 'implicitly_wait'))  # only in properties
        self.assertEquals('http://qacore02/sites/seleniumExamples/ApiDemos-debug.apk',
                          self.wrapper.config.get_optional('AppiumCapabilities', 'app'))  # only in android

    def test_configure_properties_two_files_android_first(self):
        os.environ["Files_properties"] = (os.path.join(self.root_path, 'conf', 'android-properties.cfg') + ';' +
                                          os.path.join(self.root_path, 'conf', 'properties.cfg'))
        self.wrapper.configure_properties()
        self.assertEquals('firefox', self.wrapper.config.get('Browser', 'browser'))  # get last value
        self.assertEquals('5', self.wrapper.config.get_optional('Common', 'implicitly_wait'))  # only in properties
        self.assertEquals('http://qacore02/sites/seleniumExamples/ApiDemos-debug.apk',
                          self.wrapper.config.get_optional('AppiumCapabilities', 'app'))  # only in android

    def test_configure_properties_system_property(self):
        os.environ["Files_properties"] = os.path.join(self.root_path, 'conf', 'properties.cfg')
        os.environ["Browser_browser"] = 'opera'
        self.wrapper.configure_properties()
        self.assertEquals('opera', self.wrapper.config.get('Browser', 'browser'))

    def test_configure_properties_file_not_configured(self):
        # Exception raised because default config file doesn't exist in selenium-tid-python
        self.assertRaisesRegexp(Exception, 'Properties config file not found', self.wrapper.configure_properties)

    def test_configure_properties_file_not_found(self):
        os.environ["Files_properties"] = os.path.join(self.root_path, 'conf', 'notfound-properties.cfg')
        self.assertRaisesRegexp(Exception, 'Properties config file not found', self.wrapper.configure_properties)

    def test_configure_properties_no_changes(self):
        # Configure properties
        os.environ["Files_properties"] = os.path.join(self.root_path, 'conf', 'properties.cfg')
        self.wrapper.configure_properties()
        self.assertEquals('firefox', self.wrapper.config.get('Browser', 'browser'))

        # Modify property
        new_browser = 'opera'
        self.wrapper.config.set('Browser', 'browser', new_browser)
        self.assertEquals(new_browser, self.wrapper.config.get('Browser', 'browser'))

        # Trying to configure again
        self.wrapper.configure_properties()

        # Configuration has not been initialized
        self.assertEquals(new_browser, self.wrapper.config.get('Browser', 'browser'))

    def test_configure_properties_change_configuration_file(self):
        # Configure properties
        os.environ["Files_properties"] = os.path.join(self.root_path, 'conf', 'properties.cfg')
        self.wrapper.configure_properties()
        self.assertEquals('firefox', self.wrapper.config.get('Browser', 'browser'))

        # Modify property
        new_browser = 'opera'
        self.wrapper.config.set('Browser', 'browser', new_browser)
        self.assertEquals(new_browser, self.wrapper.config.get('Browser', 'browser'))

        # Change file and try to configure again
        os.environ["Files_properties"] = os.path.join(self.root_path, 'conf', 'android-properties.cfg')
        self.wrapper.configure_properties()

        # Check that configuration has been initialized
        self.assertEquals('android', self.wrapper.config.get('Browser', 'browser'))


class SeleniumWrapperLoggerTests(SeleniumWrapperCommon):
    def setUp(self):
        self.wrapper = SeleniumWrapper()

    def test_configure_logger(self):
        os.environ["Files_logging"] = os.path.join(self.root_path, 'conf', 'logging.conf')
        self.wrapper.configure_logger()
        self.assertEquals('DEBUG', logging.getLevelName(self.wrapper.logger.getEffectiveLevel()))

    def test_configure_logger_file_not_configured(self):
        self.wrapper.configure_logger()
        self.wrapper.logger.info('No error, default logging configuration')

    def test_configure_logger_file_not_found(self):
        os.environ["Files_logging"] = os.path.join(self.root_path, 'conf', 'notfound-logging.conf')
        self.wrapper.configure_logger()
        self.wrapper.logger.info('No error, default logging configuration')

    def test_configure_logger_no_changes(self):
        # Configure logger
        os.environ["Files_logging"] = os.path.join(self.root_path, 'conf', 'logging.conf')
        self.wrapper.configure_logger()
        logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
        self.assertEquals('DEBUG', logging.getLevelName(logger.level))

        # Modify property
        new_level = 'INFO'
        logger.setLevel(new_level)
        self.assertEquals(new_level, logging.getLevelName(logger.level))

        # Trying to configure again
        self.wrapper.configure_logger()

        # Configuration has not been initialized
        self.assertEquals(new_level, logging.getLevelName(logger.level))

    def test_configure_logger_change_configuration_file(self):
        # Configure logger
        os.environ["Files_logging"] = os.path.join(self.root_path, 'conf', 'logging.conf')
        logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
        self.assertEquals('DEBUG', logging.getLevelName(logger.level))

        # Modify property
        new_level = 'INFO'
        logger.setLevel(new_level)
        self.assertEquals(new_level, logging.getLevelName(logger.level))

        # Change file and try to configure again
        os.environ["Files_logging"] = os.path.join(self.root_path, 'conf', 'warn-logging.conf')
        self.wrapper.configure_logger()

        # Check that configuration has been initialized
        self.assertEquals('WARNING', logging.getLevelName(logger.level))


mobile_tests = (
    ('android-4.1.2-on-android', True),
    ('android', True),
    ('iphone', True),
    ('firefox-4.1.2-on-android', False),
    ('firefox', False),
)

web_tests = (
    ('android-4.1.2-on-android', 'C:/TestApp.apk', None, False),
    ('android', 'C:/TestApp.apk', None, False),
    ('android', 'C:/TestApp.apk', '', False),
    ('android', None, 'chrome', True),
    ('android', None, 'chromium', True),
    ('android', None, 'browser', True),
    ('iphone', '/tmp/TestApp.zip', None, False),
    ('iphone', '/tmp/TestApp.zip', '', False),
    ('iphone', None, 'safari', True),
    ('firefox-4.1.2-on-android', None, None, True),
    ('firefox', None, None, True),
)

maximizable_browsers = (
    ('firefox-4.1.2-on-android', True),
    ('firefox', True),
    ('opera-12.12-on-xp', False),
    ('opera', False),
    ('android', False),
    ('iphone', False),
)


@ddt
class SeleniumWrapperTests(SeleniumWrapperCommon):
    def setUp(self):
        os.environ["Files_logging"] = os.path.join(self.root_path, 'conf', 'logging.conf')
        os.environ["Files_properties"] = os.path.join(self.root_path, 'conf', 'properties.cfg')
        self.wrapper = SeleniumWrapper()
        self.wrapper.configure()

    def test_singleton(self):
        # Modify first wrapper
        new_browser = 'opera'
        self.wrapper.config.set('Browser', 'browser', new_browser)

        # Request a new wrapper
        new_wrapper = SeleniumWrapper()

        # Check that wrapper and new_wrapper are the same object
        self.assertEquals(new_browser, self.wrapper.config.get('Browser', 'browser'))
        self.assertEquals(new_browser, new_wrapper.config.get('Browser', 'browser'))
        self.assertEquals(self.wrapper, new_wrapper)

    def test_configure_no_changes(self):
        # Check previous values
        self.assertEquals(1, self.wrapper.screenshots_number)

        # Modify wrapper
        self.wrapper.screenshots_number += 1

        # Trying to configure again
        self.wrapper.configure()

        # Configuration has not been initialized
        self.assertEquals(2, self.wrapper.screenshots_number)

    def test_configure_change_configuration_file(self):
        # Check previous values
        self.assertEquals('firefox', self.wrapper.config.get('Browser', 'browser'))
        self.assertEquals(1, self.wrapper.screenshots_number)

        # Modify wrapper
        self.wrapper.screenshots_number += 1

        # Change browser and try to configure again
        os.environ["Files_properties"] = os.path.join(self.root_path, 'conf', 'android-properties.cfg')
        self.wrapper.configure()

        # Check that configuration has been initialized
        self.assertEquals('android', self.wrapper.config.get('Browser', 'browser'))
        self.assertEquals(1, self.wrapper.screenshots_number)

    @mock.patch('seleniumtid.selenium_wrapper.ConfigDriver')
    def test_connect(self, ConfigDriver):
        # Mock data
        expected_driver = 'WEBDRIVER'
        instance = ConfigDriver.return_value
        instance.create_driver.return_value = expected_driver

        # Check the returned driver
        self.assertEquals(expected_driver, self.wrapper.connect())

        # Check that the wrapper has been configured
        self.assertEquals(1, self.wrapper.screenshots_number)
        self.assertEquals('firefox', self.wrapper.config.get('Browser', 'browser'))
        logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
        self.assertEquals('DEBUG', logging.getLevelName(logger.level))

    @data(*mobile_tests)
    @unpack
    def test_is_mobile_test(self, browser, is_mobile):
        self.wrapper.config.set('Browser', 'browser', browser)
        self.assertEquals(is_mobile, self.wrapper.is_mobile_test())

    @data(*web_tests)
    @unpack
    def test_is_web_test(self, browser, appium_app, appium_browser_name, is_web):
        self.wrapper.config.set('Browser', 'browser', browser)
        self.wrapper.config.set('AppiumCapabilities', 'app', appium_app)
        self.wrapper.config.set('AppiumCapabilities', 'browserName', appium_browser_name)
        self.assertEquals(is_web, self.wrapper.is_web_test())

    @data(*maximizable_browsers)
    @unpack
    def test_is_maximizable(self, browser, is_maximizable):
        self.wrapper.config.set('Browser', 'browser', browser)
        self.assertEquals(is_maximizable, self.wrapper.is_maximizable())
