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
from nose.tools import assert_equal, assert_not_equal, assert_in, assert_raises

from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool


class DriverWrapperCommon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_path = os.path.dirname(os.path.realpath(__file__))

    def tearDown(self):
        # Remove environment properties
        try:
            del os.environ["Config_log_filename"]
            del os.environ["Config_prop_filenames"]
            del os.environ["Driver_type"]
        except KeyError:
            pass


class DriverWrapperPropertiesTests(DriverWrapperCommon):
    def setUp(self):
        os.environ["Config_log_filename"] = 'logging.conf'

        # Reset wrappers pool values
        DriverWrappersPool._empty_pool()
        DriverWrapper.config_properties_filenames = None

        # Create a new wrapper
        self.driver_wrapper = DriverWrappersPool.get_default_wrapper()

        config_files = ConfigFiles()
        config_files.set_config_directory(os.path.join(self.root_path, 'conf'))
        config_files.set_output_directory(os.path.join(self.root_path, 'output'))
        DriverWrappersPool.configure_common_directories(config_files)
        self.driver_wrapper.configure_logger()

    def test_configure_properties(self):
        os.environ["Config_prop_filenames"] = 'properties.cfg'
        self.driver_wrapper.configure_properties()
        assert_equal('firefox', self.driver_wrapper.config.get('Driver', 'type'))  # get last value
        assert_equal('5', self.driver_wrapper.config.get_optional('Driver', 'implicitly_wait'))  # only in properties
        assert_equal(None, self.driver_wrapper.config.get_optional('AppiumCapabilities', 'app'))  # only in android

    def test_configure_properties_android(self):
        os.environ["Config_prop_filenames"] = 'android-properties.cfg'
        self.driver_wrapper.configure_properties()
        assert_equal('android', self.driver_wrapper.config.get('Driver', 'type'))  # get last value
        assert_equal(None, self.driver_wrapper.config.get_optional('Driver', 'implicitly_wait'))  # only in properties
        assert_equal('http://invented_url/Demo.apk',
                     self.driver_wrapper.config.get_optional('AppiumCapabilities', 'app'))  # only in android

    def test_configure_properties_two_files(self):
        os.environ["Config_prop_filenames"] = 'properties.cfg;android-properties.cfg'
        self.driver_wrapper.configure_properties()
        assert_equal('android', self.driver_wrapper.config.get('Driver', 'type'))  # get last value
        assert_equal('5', self.driver_wrapper.config.get_optional('Driver', 'implicitly_wait'))  # only in properties
        assert_equal('http://invented_url/Demo.apk',
                     self.driver_wrapper.config.get_optional('AppiumCapabilities', 'app'))  # only in android

    def test_configure_properties_two_files_android_first(self):
        os.environ["Config_prop_filenames"] = 'android-properties.cfg;properties.cfg'
        self.driver_wrapper.configure_properties()
        assert_equal('firefox', self.driver_wrapper.config.get('Driver', 'type'))  # get last value
        assert_equal('5', self.driver_wrapper.config.get_optional('Driver', 'implicitly_wait'))  # only in properties
        assert_equal('http://invented_url/Demo.apk',
                     self.driver_wrapper.config.get_optional('AppiumCapabilities', 'app'))  # only in android

    def test_configure_properties_system_property(self):
        os.environ["Config_prop_filenames"] = 'properties.cfg'
        os.environ["Driver_type"] = 'opera'
        self.driver_wrapper.configure_properties()
        assert_equal('opera', self.driver_wrapper.config.get('Driver', 'type'))

    def test_configure_properties_file_default_file(self):
        self.driver_wrapper.configure_properties()
        assert_equal('firefox', self.driver_wrapper.config.get('Driver', 'type'))

    def test_configure_properties_file_not_found(self):
        os.environ["Config_prop_filenames"] = 'notfound-properties.cfg'
        with assert_raises(Exception) as cm:
            self.driver_wrapper.configure_properties()
        assert_in('Properties config file not found', str(cm.exception))

    def test_configure_properties_no_changes(self):
        # Configure properties
        os.environ["Config_prop_filenames"] = 'properties.cfg'
        self.driver_wrapper.configure_properties()
        assert_equal('firefox', self.driver_wrapper.config.get('Driver', 'type'))

        # Modify property
        new_driver_type = 'opera'
        self.driver_wrapper.config.set('Driver', 'type', new_driver_type)
        assert_equal(new_driver_type, self.driver_wrapper.config.get('Driver', 'type'))

        # Trying to configure again
        self.driver_wrapper.configure_properties()

        # Configuration has not been initialized
        assert_equal(new_driver_type, self.driver_wrapper.config.get('Driver', 'type'))

    def test_configure_properties_change_configuration_file(self):
        # Configure properties
        os.environ["Config_prop_filenames"] = 'properties.cfg'
        self.driver_wrapper.configure_properties()
        assert_equal('firefox', self.driver_wrapper.config.get('Driver', 'type'))

        # Modify property
        new_driver_type = 'opera'
        self.driver_wrapper.config.set('Driver', 'type', new_driver_type)
        assert_equal(new_driver_type, self.driver_wrapper.config.get('Driver', 'type'))

        # Change file and try to configure again
        os.environ["Config_prop_filenames"] = 'android-properties.cfg'
        self.driver_wrapper.configure_properties()

        # Check that configuration has been initialized
        assert_equal('android', self.driver_wrapper.config.get('Driver', 'type'))


class DriverWrapperLoggerTests(DriverWrapperCommon):
    def setUp(self):
        self.driver_wrapper = DriverWrappersPool.get_default_wrapper()
        config_files = ConfigFiles()
        config_files.set_config_directory(os.path.join(self.root_path, 'conf'))
        config_files.set_output_directory(os.path.join(self.root_path, 'output'))
        DriverWrappersPool.configure_common_directories(config_files)

    def test_configure_logger(self):
        os.environ["Config_log_filename"] = 'logging.conf'
        self.driver_wrapper.configure_logger()
        assert_equal('DEBUG', logging.getLevelName(self.driver_wrapper.logger.getEffectiveLevel()))

    def test_configure_logger_file_not_configured(self):
        self.driver_wrapper.configure_logger()
        self.driver_wrapper.logger.info('No error, default logging configuration')

    def test_configure_logger_file_not_found(self):
        os.environ["Config_log_filename"] = 'notfound-logging.conf'
        self.driver_wrapper.configure_logger()
        self.driver_wrapper.logger.info('No error, default logging configuration')

    def test_configure_logger_no_changes(self):
        # Configure logger
        os.environ["Config_log_filename"] = 'logging.conf'
        self.driver_wrapper.configure_logger()
        logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
        assert_equal('DEBUG', logging.getLevelName(logger.level))

        # Modify property
        new_level = 'INFO'
        logger.setLevel(new_level)
        assert_equal(new_level, logging.getLevelName(logger.level))

        # Trying to configure again
        self.driver_wrapper.configure_logger()

        # Configuration has not been initialized
        assert_equal(new_level, logging.getLevelName(logger.level))

    def test_configure_logger_change_configuration_file(self):
        # Configure logger
        os.environ["Config_log_filename"] = 'logging.conf'
        logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
        assert_equal('DEBUG', logging.getLevelName(logger.level))

        # Modify property
        new_level = 'INFO'
        logger.setLevel(new_level)
        assert_equal(new_level, logging.getLevelName(logger.level))

        # Change file and try to configure again
        os.environ["Config_log_filename"] = 'warn-logging.conf'
        self.driver_wrapper.configure_logger()

        # Check that configuration has been initialized
        assert_equal('WARNING', logging.getLevelName(logger.level))


class DriverWrapperBaselineTests(DriverWrapperCommon):
    def setUp(self):
        # Reset wrappers pool values
        DriverWrappersPool._empty_pool()
        DriverWrapper.config_properties_filenames = None

        # Create a new wrapper
        self.driver_wrapper = DriverWrappersPool.get_default_wrapper()

        config_files = ConfigFiles()
        config_files.set_config_directory(os.path.join(self.root_path, 'conf'))
        config_files.set_output_directory(os.path.join(self.root_path, 'output'))
        DriverWrappersPool.configure_common_directories(config_files)
        self.driver_wrapper.configure_properties()

    def test_configure_visual_baseline_not_configured(self):
        self.driver_wrapper.config.remove_option('VisualTests', 'baseline_name')

        self.driver_wrapper.configure_visual_baseline()

        expected_baseline_directory = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox')
        assert_equal(self.driver_wrapper.baseline_name, 'firefox')
        assert_equal(self.driver_wrapper.visual_baseline_directory, expected_baseline_directory)

    def test_configure_visual_baseline_driver_type(self):
        self.driver_wrapper.config.set('VisualTests', 'baseline_name', '{Driver_type}')

        self.driver_wrapper.configure_visual_baseline()

        expected_baseline_directory = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox')
        assert_equal(self.driver_wrapper.baseline_name, 'firefox')
        assert_equal(self.driver_wrapper.visual_baseline_directory, expected_baseline_directory)

    def test_update_visual_baseline_platform_version(self):
        # Configure baseline and driver mock
        self.driver_wrapper.config.set('VisualTests', 'baseline_name', 'ios_{PlatformVersion}')
        self.driver_wrapper.driver = mock.MagicMock()
        self.driver_wrapper.driver.desired_capabilities.__getitem__.return_value = '9.3'

        self.driver_wrapper.configure_visual_baseline()
        self.driver_wrapper.update_visual_baseline()

        expected_baseline_directory = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'ios_9.3')
        assert_equal(self.driver_wrapper.baseline_name, 'ios_9.3')
        assert_equal(self.driver_wrapper.visual_baseline_directory, expected_baseline_directory)

    def test_update_visual_baseline_remote_node(self):
        # Configure baseline and remote node
        self.driver_wrapper.config.set('VisualTests', 'baseline_name', 'firefox_{RemoteNode}')
        self.driver_wrapper.remote_node = '255.255.255.255'

        self.driver_wrapper.configure_visual_baseline()
        self.driver_wrapper.update_visual_baseline()

        expected_baseline_directory = os.path.join(self.root_path, 'output', 'visualtests', 'baseline',
                                                   'firefox_255.255.255.255')
        assert_equal(self.driver_wrapper.baseline_name, 'firefox_255.255.255.255')
        assert_equal(self.driver_wrapper.visual_baseline_directory, expected_baseline_directory)

    def test_update_visual_baseline_remote_node_empty(self):
        # Configure baseline
        self.driver_wrapper.config.set('VisualTests', 'baseline_name', 'firefox_{RemoteNode}')

        self.driver_wrapper.configure_visual_baseline()
        self.driver_wrapper.update_visual_baseline()

        expected_baseline_directory = os.path.join(self.root_path, 'output', 'visualtests', 'baseline', 'firefox_None')
        assert_equal(self.driver_wrapper.baseline_name, 'firefox_None')
        assert_equal(self.driver_wrapper.visual_baseline_directory, expected_baseline_directory)


# (driver_type, is_mobile, is_android, is_ios)
mobile_tests = (
    ('android-4.1.2-on-android', True, True, False),
    ('android', True, True, False),
    ('ios', True, False, True),
    ('iphone', True, False, True),
    ('firefox-4.1.2-on-android', False, False, False),
    ('firefox', False, False, False),
)

# (driver_type, appium_app, appium_browser_name, is_web, is_android_web, is_ios_web)
web_tests = (
    ('android-4.1.2-on-android', 'C:/Demo.apk', None, False, False, False),
    ('android', 'C:/Demo.apk', None, False, False, False),
    ('android', 'C:/Demo.apk', '', False, False, False),
    ('android', None, 'chrome', True, True, False),
    ('android', None, 'chromium', True, True, False),
    ('android', None, 'browser', True, True, False),
    ('ios', '/tmp/Demo.zip', None, False, False, False),
    ('ios', '/tmp/Demo.zip', '', False, False, False),
    ('ios', None, 'safari', True, False, True),
    ('iphone', '/tmp/Demo.zip', None, False, False, False),
    ('iphone', '/tmp/Demo.zip', '', False, False, False),
    ('iphone', None, 'safari', True, False, True),
    ('firefox-4.1.2-on-android', None, None, True, False, False),
    ('firefox', None, None, True, False, False),
)

# (driver_type, is_maximizable)
maximizable_drivers = (
    ('firefox-4.1.2-on-android', True),
    ('firefox', True),
    ('opera-12.12-on-xp', True),
    ('opera', True),
    ('edge', True),
    ('android', False),
    ('ios', False),
    ('iphone', False),
)


@ddt
class DriverWrapperTests(DriverWrapperCommon):
    def setUp(self):
        os.environ["Config_log_filename"] = os.path.join(self.root_path, 'conf', 'logging.conf')
        os.environ["Config_prop_filenames"] = os.path.join(self.root_path, 'conf', 'properties.cfg')
        self.driver_wrapper = DriverWrapper()
        self.driver_wrapper.configure()

    def test_multiple(self):
        # Request a new additional wrapper
        new_wrapper = DriverWrapper()

        # Modify new wrapper
        first_driver_type = 'firefox'
        new_driver_type = 'opera'
        new_wrapper.config.set('Driver', 'type', new_driver_type)

        # Check that wrapper and new_wrapper are different
        assert_equal(first_driver_type, self.driver_wrapper.config.get('Driver', 'type'))
        assert_equal(new_driver_type, new_wrapper.config.get('Driver', 'type'))
        assert_not_equal(self.driver_wrapper, new_wrapper)

    def test_configure_no_changes(self):
        # Check previous values
        assert_equal('firefox', self.driver_wrapper.config.get('Driver', 'type'))

        # Modify wrapper
        self.driver_wrapper.config.set('Driver', 'type', 'opera')

        # Trying to configure again
        self.driver_wrapper.configure()

        # Configuration has not been initialized
        assert_equal('opera', self.driver_wrapper.config.get('Driver', 'type'))

    def test_configure_change_configuration_file(self):
        # Check previous values
        assert_equal('firefox', self.driver_wrapper.config.get('Driver', 'type'))

        # Modify wrapper
        self.driver_wrapper.config.set('Driver', 'type', 'opera')

        # Change driver type and try to configure again
        os.environ["Config_prop_filenames"] = os.path.join(self.root_path, 'conf', 'android-properties.cfg')
        self.driver_wrapper.configure()

        # Check that configuration has been initialized
        assert_equal('android', self.driver_wrapper.config.get('Driver', 'type'))

    @mock.patch('toolium.driver_wrapper.ConfigDriver')
    def test_connect(self, ConfigDriver):
        # Mock data
        expected_driver = mock.MagicMock()
        instance = ConfigDriver.return_value
        instance.create_driver.return_value = expected_driver
        self.driver_wrapper.utils = mock.MagicMock()

        # Connect and check the returned driver
        assert_equal(expected_driver, self.driver_wrapper.connect(maximize=False))

        # Check that the wrapper has been configured
        assert_equal('firefox', self.driver_wrapper.config.get('Driver', 'type'))
        logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
        assert_equal('DEBUG', logging.getLevelName(logger.level))

    def test_connect_api(self):
        # Mock data
        expected_driver = None

        # Change driver type to api and configure again
        os.environ["Config_prop_filenames"] = os.path.join(self.root_path, 'conf', 'api-properties.cfg')
        self.driver_wrapper.configure()

        # Connect and check that the returned driver is None
        self.driver_wrapper.configure()
        assert_equal(expected_driver, self.driver_wrapper.connect(maximize=False))

        # Check that the wrapper has been configured
        assert_equal('', self.driver_wrapper.config.get('Driver', 'type'))
        assert_equal('false', self.driver_wrapper.config.get('Jira', 'enabled'))
        logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
        assert_equal('DEBUG', logging.getLevelName(logger.level))

    @data(*mobile_tests)
    @unpack
    def test_is_mobile_test(self, driver_type, is_mobile, is_android, is_ios):
        self.driver_wrapper.config.set('Driver', 'type', driver_type)
        assert_equal(is_mobile, self.driver_wrapper.is_mobile_test())
        assert_equal(is_android, self.driver_wrapper.is_android_test())
        assert_equal(is_ios, self.driver_wrapper.is_ios_test())

    @data(*web_tests)
    @unpack
    def test_is_web_test(self, driver_type, appium_app, appium_browser_name, is_web, is_android_web, is_ios_web):
        self.driver_wrapper.config.set('Driver', 'type', driver_type)
        if appium_app is not None:
            self.driver_wrapper.config.set('AppiumCapabilities', 'app', appium_app)
        if appium_browser_name is not None:
            self.driver_wrapper.config.set('AppiumCapabilities', 'browserName', appium_browser_name)
        assert_equal(is_web, self.driver_wrapper.is_web_test())
        assert_equal(is_android_web, self.driver_wrapper.is_android_web_test())
        assert_equal(is_ios_web, self.driver_wrapper.is_ios_web_test())

    @data(*maximizable_drivers)
    @unpack
    def test_is_maximizable(self, driver_type, is_maximizable):
        self.driver_wrapper.config.set('Driver', 'type', driver_type)
        assert_equal(is_maximizable, self.driver_wrapper.is_maximizable())
