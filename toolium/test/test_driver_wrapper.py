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
import os
import unittest

import mock
from ddt import ddt, data, unpack

from toolium.driver_wrapper import DriverWrapper


class DriverWrapperCommon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_path = os.path.dirname(os.path.realpath(__file__))

    def tearDown(self):
        # Remove environment properties
        try:
            del os.environ["Config_log_filename"]
            del os.environ["Config_prop_filenames"]
            del os.environ["Browser_browser"]
        except KeyError:
            pass
        # Remove previous wrapper instance
        DriverWrapper._instance = None


class DriverWrapperPropertiesTests(DriverWrapperCommon):
    def setUp(self):
        os.environ["Config_log_filename"] = os.path.join(self.root_path, 'conf', 'logging.conf')
        self.wrapper = DriverWrapper(main_driver=True)
        self.wrapper.config_directory = ''
        self.wrapper.output_directory = ''
        self.wrapper.configure_logger()

    def test_configure_properties(self):
        os.environ["Config_prop_filenames"] = os.path.join(self.root_path, 'conf', 'properties.cfg')
        self.wrapper.configure_properties()
        self.assertEqual('firefox', self.wrapper.config.get('Browser', 'browser'))  # get last value
        self.assertEqual('5', self.wrapper.config.get_optional('Common', 'implicitly_wait'))  # only in properties
        self.assertEqual(None, self.wrapper.config.get_optional('AppiumCapabilities', 'app'))  # only in android

    def test_configure_properties_android(self):
        os.environ["Config_prop_filenames"] = os.path.join(self.root_path, 'conf', 'android-properties.cfg')
        self.wrapper.configure_properties()
        self.assertEqual('android', self.wrapper.config.get('Browser', 'browser'))  # get last value
        self.assertEqual(None, self.wrapper.config.get_optional('Common', 'implicitly_wait'))  # only in properties
        self.assertEqual('http://invented_url/Demo.apk',
                         self.wrapper.config.get_optional('AppiumCapabilities', 'app'))  # only in android

    def test_configure_properties_two_files(self):
        os.environ["Config_prop_filenames"] = (os.path.join(self.root_path, 'conf', 'properties.cfg') + ';' +
                                               os.path.join(self.root_path, 'conf', 'android-properties.cfg'))
        self.wrapper.configure_properties()
        self.assertEqual('android', self.wrapper.config.get('Browser', 'browser'))  # get last value
        self.assertEqual('5', self.wrapper.config.get_optional('Common', 'implicitly_wait'))  # only in properties
        self.assertEqual('http://invented_url/Demo.apk',
                         self.wrapper.config.get_optional('AppiumCapabilities', 'app'))  # only in android

    def test_configure_properties_two_files_android_first(self):
        os.environ["Config_prop_filenames"] = (os.path.join(self.root_path, 'conf', 'android-properties.cfg') + ';' +
                                               os.path.join(self.root_path, 'conf', 'properties.cfg'))
        self.wrapper.configure_properties()
        self.assertEqual('firefox', self.wrapper.config.get('Browser', 'browser'))  # get last value
        self.assertEqual('5', self.wrapper.config.get_optional('Common', 'implicitly_wait'))  # only in properties
        self.assertEqual('http://invented_url/Demo.apk',
                         self.wrapper.config.get_optional('AppiumCapabilities', 'app'))  # only in android

    def test_configure_properties_system_property(self):
        os.environ["Config_prop_filenames"] = os.path.join(self.root_path, 'conf', 'properties.cfg')
        os.environ["Browser_browser"] = 'opera'
        self.wrapper.configure_properties()
        self.assertEqual('opera', self.wrapper.config.get('Browser', 'browser'))

    def test_configure_properties_file_not_configured(self):
        # Exception raised because in this case default config file doesn't exist
        with self.assertRaises(Exception) as cm:
            self.wrapper.configure_properties()
        self.assertIn('Properties config file not found', str(cm.exception))

    def test_configure_properties_file_not_found(self):
        os.environ["Config_prop_filenames"] = os.path.join(self.root_path, 'conf', 'notfound-properties.cfg')
        with self.assertRaises(Exception) as cm:
            self.wrapper.configure_properties()
        self.assertIn('Properties config file not found', str(cm.exception))

    def test_configure_properties_no_changes(self):
        # Configure properties
        os.environ["Config_prop_filenames"] = os.path.join(self.root_path, 'conf', 'properties.cfg')
        self.wrapper.configure_properties()
        self.assertEqual('firefox', self.wrapper.config.get('Browser', 'browser'))

        # Modify property
        new_browser = 'opera'
        self.wrapper.config.set('Browser', 'browser', new_browser)
        self.assertEqual(new_browser, self.wrapper.config.get('Browser', 'browser'))

        # Trying to configure again
        self.wrapper.configure_properties()

        # Configuration has not been initialized
        self.assertEqual(new_browser, self.wrapper.config.get('Browser', 'browser'))

    def test_configure_properties_change_configuration_file(self):
        # Configure properties
        os.environ["Config_prop_filenames"] = os.path.join(self.root_path, 'conf', 'properties.cfg')
        self.wrapper.configure_properties()
        self.assertEqual('firefox', self.wrapper.config.get('Browser', 'browser'))

        # Modify property
        new_browser = 'opera'
        self.wrapper.config.set('Browser', 'browser', new_browser)
        self.assertEqual(new_browser, self.wrapper.config.get('Browser', 'browser'))

        # Change file and try to configure again
        os.environ["Config_prop_filenames"] = os.path.join(self.root_path, 'conf', 'android-properties.cfg')
        self.wrapper.configure_properties()

        # Check that configuration has been initialized
        self.assertEqual('android', self.wrapper.config.get('Browser', 'browser'))


class DriverWrapperLoggerTests(DriverWrapperCommon):
    def setUp(self):
        self.wrapper = DriverWrapper(main_driver=True)
        self.wrapper.config_directory = ''
        self.wrapper.output_directory = ''

    def test_configure_logger(self):
        os.environ["Config_log_filename"] = os.path.join(self.root_path, 'conf', 'logging.conf')
        self.wrapper.configure_logger()
        self.assertEqual('DEBUG', logging.getLevelName(self.wrapper.logger.getEffectiveLevel()))

    def test_configure_logger_file_not_configured(self):
        self.wrapper.configure_logger()
        self.wrapper.logger.info('No error, default logging configuration')

    def test_configure_logger_file_not_found(self):
        os.environ["Config_log_filename"] = os.path.join(self.root_path, 'conf', 'notfound-logging.conf')
        self.wrapper.configure_logger()
        self.wrapper.logger.info('No error, default logging configuration')

    def test_configure_logger_no_changes(self):
        # Configure logger
        os.environ["Config_log_filename"] = os.path.join(self.root_path, 'conf', 'logging.conf')
        self.wrapper.configure_logger()
        logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
        self.assertEqual('DEBUG', logging.getLevelName(logger.level))

        # Modify property
        new_level = 'INFO'
        logger.setLevel(new_level)
        self.assertEqual(new_level, logging.getLevelName(logger.level))

        # Trying to configure again
        self.wrapper.configure_logger()

        # Configuration has not been initialized
        self.assertEqual(new_level, logging.getLevelName(logger.level))

    def test_configure_logger_change_configuration_file(self):
        # Configure logger
        os.environ["Config_log_filename"] = os.path.join(self.root_path, 'conf', 'logging.conf')
        logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
        self.assertEqual('DEBUG', logging.getLevelName(logger.level))

        # Modify property
        new_level = 'INFO'
        logger.setLevel(new_level)
        self.assertEqual(new_level, logging.getLevelName(logger.level))

        # Change file and try to configure again
        os.environ["Config_log_filename"] = os.path.join(self.root_path, 'conf', 'warn-logging.conf')
        self.wrapper.configure_logger()

        # Check that configuration has been initialized
        self.assertEqual('WARNING', logging.getLevelName(logger.level))


mobile_tests = (
    ('android-4.1.2-on-android', True),
    ('android', True),
    ('ios', True),
    ('iphone', True),
    ('firefox-4.1.2-on-android', False),
    ('firefox', False),
)

web_tests = (
    ('android-4.1.2-on-android', 'C:/Demo.apk', None, False),
    ('android', 'C:/Demo.apk', None, False),
    ('android', 'C:/Demo.apk', '', False),
    ('android', None, 'chrome', True),
    ('android', None, 'chromium', True),
    ('android', None, 'browser', True),
    ('ios', '/tmp/Demo.zip', None, False),
    ('ios', '/tmp/Demo.zip', '', False),
    ('ios', None, 'safari', True),
    ('iphone', '/tmp/Demo.zip', None, False),
    ('iphone', '/tmp/Demo.zip', '', False),
    ('iphone', None, 'safari', True),
    ('firefox-4.1.2-on-android', None, None, True),
    ('firefox', None, None, True),
)

maximizable_browsers = (
    ('firefox-4.1.2-on-android', True),
    ('firefox', True),
    ('opera-12.12-on-xp', True),
    ('opera', True),
    ('edge', False),
    ('android', False),
    ('ios', False),
    ('iphone', False),
)


@ddt
class DriverWrapperTests(DriverWrapperCommon):
    def setUp(self):
        os.environ["Config_log_filename"] = os.path.join(self.root_path, 'conf', 'logging.conf')
        os.environ["Config_prop_filenames"] = os.path.join(self.root_path, 'conf', 'properties.cfg')
        self.driver_wrapper = DriverWrapper(main_driver=True)
        self.driver_wrapper.configure()

    def test_singleton(self):
        # Request a new main wrapper
        new_wrapper = DriverWrapper(main_driver=True)

        # Modify new wrapper
        new_browser = 'opera'
        new_wrapper.config.set('Browser', 'browser', new_browser)

        # Check that both wrappers are the same object
        self.assertEqual(new_browser, self.driver_wrapper.config.get('Browser', 'browser'))
        self.assertEqual(new_browser, new_wrapper.config.get('Browser', 'browser'))
        self.assertEqual(self.driver_wrapper, new_wrapper)

    def test_multiple(self):
        # Request a new additional wrapper
        new_wrapper = DriverWrapper()

        # Modify new wrapper
        first_browser = 'firefox'
        new_browser = 'opera'
        new_wrapper.config.set('Browser', 'browser', new_browser)

        # Check that wrapper and new_wrapper are different
        self.assertEqual(first_browser, self.driver_wrapper.config.get('Browser', 'browser'))
        self.assertEqual(new_browser, new_wrapper.config.get('Browser', 'browser'))
        self.assertNotEqual(self.driver_wrapper, new_wrapper)

    def test_configure_no_changes(self):
        # Check previous values
        self.assertEqual(1, self.driver_wrapper.screenshots_number)

        # Modify wrapper
        self.driver_wrapper.screenshots_number += 1

        # Trying to configure again
        self.driver_wrapper.configure()

        # Configuration has not been initialized
        self.assertEqual(2, self.driver_wrapper.screenshots_number)

    def test_configure_change_configuration_file(self):
        # Check previous values
        self.assertEqual('firefox', self.driver_wrapper.config.get('Browser', 'browser'))
        self.assertEqual(1, self.driver_wrapper.screenshots_number)

        # Modify wrapper
        self.driver_wrapper.screenshots_number += 1

        # Change browser and try to configure again
        os.environ["Config_prop_filenames"] = os.path.join(self.root_path, 'conf', 'android-properties.cfg')
        self.driver_wrapper.configure()

        # Check that configuration has been initialized
        self.assertEqual('android', self.driver_wrapper.config.get('Browser', 'browser'))
        self.assertEqual(1, self.driver_wrapper.screenshots_number)

    @mock.patch('toolium.driver_wrapper.ConfigDriver')
    def test_connect(self, ConfigDriver):
        # Mock data
        expected_driver = 'WEBDRIVER'
        instance = ConfigDriver.return_value
        instance.create_driver.return_value = expected_driver

        # Check the returned driver
        self.driver_wrapper.configure()
        self.assertEqual(expected_driver, self.driver_wrapper.connect(maximize=False))

        # Check that the wrapper has been configured
        self.assertEqual(1, self.driver_wrapper.screenshots_number)
        self.assertEqual('firefox', self.driver_wrapper.config.get('Browser', 'browser'))
        logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
        self.assertEqual('DEBUG', logging.getLevelName(logger.level))

    @data(*mobile_tests)
    @unpack
    def test_is_mobile_test(self, browser, is_mobile):
        self.driver_wrapper.config.set('Browser', 'browser', browser)
        self.assertEqual(is_mobile, self.driver_wrapper.is_mobile_test())

    @data(*web_tests)
    @unpack
    def test_is_web_test(self, browser, appium_app, appium_browser_name, is_web):
        self.driver_wrapper.config.set('Browser', 'browser', browser)
        if appium_app is not None:
            self.driver_wrapper.config.set('AppiumCapabilities', 'app', appium_app)
        if appium_browser_name is not None:
            self.driver_wrapper.config.set('AppiumCapabilities', 'browserName', appium_browser_name)
        self.assertEqual(is_web, self.driver_wrapper.is_web_test())

    @data(*maximizable_browsers)
    @unpack
    def test_is_maximizable(self, browser, is_maximizable):
        self.driver_wrapper.config.set('Browser', 'browser', browser)
        self.assertEqual(is_maximizable, self.driver_wrapper.is_maximizable())
