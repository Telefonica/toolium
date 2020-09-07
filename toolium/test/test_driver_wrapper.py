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

import mock
import pytest

from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool

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
    ('android-4.1.2-on-android', 'C:/Demo.apk', None, False, False,
     False),
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


@pytest.fixture
def driver_wrapper():
    # Reset wrappers pool values
    DriverWrappersPool._empty_pool()
    DriverWrapper.config_properties_filenames = None

    # Create a new wrapper
    new_driver_wrapper = DriverWrappersPool.get_default_wrapper()

    # Configure wrapper
    config_files = ConfigFiles()
    root_path = os.path.dirname(os.path.realpath(__file__))
    config_files.set_config_directory(os.path.join(root_path, 'conf'))
    config_files.set_output_directory(os.path.join(root_path, 'output'))
    config_files.set_config_log_filename('logging.conf')
    new_driver_wrapper.configure(config_files)

    return new_driver_wrapper


def test_multiple(driver_wrapper):
    # Request a new additional wrapper
    new_wrapper = DriverWrapper()

    # Modify new wrapper
    first_driver_type = 'firefox'
    new_driver_type = 'opera'
    new_wrapper.config.set('Driver', 'type', new_driver_type)

    # Check that wrapper and new_wrapper are different
    assert driver_wrapper.config.get('Driver', 'type') == first_driver_type
    assert new_wrapper.config.get('Driver', 'type') == new_driver_type
    assert new_wrapper != driver_wrapper


def test_configure_no_changes(driver_wrapper):
    # Check previous values
    assert driver_wrapper.config.get('Driver', 'type') == 'firefox'

    # Modify wrapper
    driver_wrapper.config.set('Driver', 'type', 'opera')

    # Trying to configure again
    driver_wrapper.configure(ConfigFiles())

    # Configuration has not been initialized
    assert driver_wrapper.config.get('Driver', 'type') == 'opera'


def test_configure_change_configuration_file(driver_wrapper):
    # Check previous values
    assert driver_wrapper.config.get('Driver', 'type') == 'firefox'

    # Modify wrapper
    driver_wrapper.config.set('Driver', 'type', 'opera')

    # Change properties file and try to configure again
    root_path = os.path.dirname(os.path.realpath(__file__))
    os.environ["Config_prop_filenames"] = os.path.join(root_path, 'conf', 'android-properties.cfg')
    driver_wrapper.configure(ConfigFiles())
    del os.environ["Config_prop_filenames"]

    # Check that configuration has been initialized
    assert driver_wrapper.config.get('Driver', 'type') == 'android'


def test_configure_environment(driver_wrapper):
    # Check previous values
    assert driver_wrapper.config.get('Driver', 'type') == 'firefox'

    # Change environment and try to configure again
    os.environ["Config_environment"] = 'android'
    config_files = DriverWrappersPool.initialize_config_files(ConfigFiles())
    driver_wrapper.configure(config_files)
    del os.environ["Config_environment"]

    # Check that configuration has been initialized
    assert driver_wrapper.config.get('Driver', 'type') == 'android'


@mock.patch('toolium.driver_wrapper.ConfigDriver.create_driver')
def test_connect(create_driver, driver_wrapper):
    # Mock data
    expected_driver = mock.MagicMock()
    create_driver.return_value = expected_driver
    driver_wrapper.utils = mock.MagicMock()
    driver_wrapper.utils.get_remote_node.return_value = ('local', None)

    # Connect and check the returned driver
    assert driver_wrapper.connect(maximize=False) == expected_driver

    # Check that the wrapper has been configured
    assert driver_wrapper.config.get('Driver', 'type') == 'firefox'
    logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
    assert logging.getLevelName(logger.level) == 'DEBUG'


api_tests = (
    '',
    'api',
    'no_driver',
)


@pytest.mark.parametrize("driver_type", api_tests)
def test_connect_api(driver_type, driver_wrapper):
    # Mock data
    expected_driver = None
    driver_wrapper.config.set('Driver', 'type', driver_type)

    # Connect and check that the returned driver is None
    assert driver_wrapper.connect(maximize=False) == expected_driver  # Check that the wrapper has been configured
    assert driver_wrapper.config.get('Driver', 'type') == driver_type
    assert driver_wrapper.config.get('Jira', 'enabled') == 'false'
    logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
    assert logging.getLevelName(logger.level) == 'DEBUG'


def test_connect_api_from_file(driver_wrapper):
    # Mock data
    expected_driver = None

    # Change driver type to api and configure again
    root_path = os.path.dirname(os.path.realpath(__file__))
    os.environ["Config_prop_filenames"] = os.path.join(root_path, 'conf', 'api-properties.cfg')
    driver_wrapper.configure(ConfigFiles())
    del os.environ["Config_prop_filenames"]

    # Connect and check that the returned driver is None
    assert driver_wrapper.connect(maximize=False) == expected_driver  # Check that the wrapper has been configured
    assert driver_wrapper.config.get('Driver', 'type') == ''
    assert driver_wrapper.config.get('Jira', 'enabled') == 'false'
    logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
    assert logging.getLevelName(logger.level) == 'DEBUG'


@pytest.mark.parametrize("driver_type, is_mobile, is_android, is_ios", mobile_tests)
def test_is_mobile_test(driver_type, is_mobile, is_android, is_ios, driver_wrapper):
    driver_wrapper.config.set('Driver', 'type', driver_type)
    assert driver_wrapper.is_mobile_test() == is_mobile
    assert driver_wrapper.is_android_test() == is_android
    assert driver_wrapper.is_ios_test() == is_ios


@pytest.mark.parametrize("driver_type, appium_app, appium_browser_name, is_web, is_android_web, is_ios_web", web_tests)
def test_is_web_test(driver_type, appium_app, appium_browser_name, is_web, is_android_web, is_ios_web, driver_wrapper):
    driver_wrapper.config.set('Driver', 'type', driver_type)
    if appium_app is not None:
        driver_wrapper.config.set('AppiumCapabilities', 'app', appium_app)
    if appium_browser_name is not None:
        driver_wrapper.config.set('AppiumCapabilities', 'browserName', appium_browser_name)
    assert driver_wrapper.is_web_test() == is_web
    assert driver_wrapper.is_android_web_test() == is_android_web
    assert driver_wrapper.is_ios_web_test() == is_ios_web


@pytest.mark.parametrize("driver_type, is_maximizable", maximizable_drivers)
def test_is_maximizable(driver_type, is_maximizable, driver_wrapper):
    driver_wrapper.config.set('Driver', 'type', driver_type)
    assert driver_wrapper.is_maximizable() == is_maximizable


# (reuse_driver, reuse_driver_session, restart_driver_after_failure, restart_driver_fail,
#  reuse_driver_from_tags, scope, test_passed, expected_should_reuse_driver)
should_be_reused = (
    ('true', 'true', 'true', 'true', True, 'function', True, True),  # all = true
    # reuse_driver
    ('true', 'false', 'false', 'false', False, 'function', True, True),  # reuse = true, function
    ('true', 'false', 'false', 'false', False, 'module', True, False),  # reuse = true, module
    ('true', 'false', 'false', 'false', False, 'session', True, False),  # reuse = true, session
    ('false', 'false', 'false', 'false', False, 'function', True, False),  # reuse = false
    # restart_driver_after_failure
    ('true', 'false', 'false', 'false', False, 'function', True, True),  # restart = false, test passed
    ('true', 'false', 'true', 'false', False, 'function', True, True),  # restart = true, test passed
    ('true', 'false', 'false', 'false', False, 'function', False, True),  # restart = false, test failed
    ('true', 'false', 'true', 'false', False, 'function', False, False),  # restart = true, test failed
    # restart_driver_fail (deprecated)
    ('true', 'false', 'false', 'false', False, 'function', True, True),  # restart = false, test passed
    ('true', 'false', 'false', 'true', False, 'function', True, True),  # restart = true, test passed
    ('true', 'false', 'false', 'false', False, 'function', False, True),  # restart = false, test failed
    ('true', 'false', 'false', 'true', False, 'function', False, False),  # restart = true, test failed
    # reuse_driver_session
    ('false', 'true', 'false', 'false', False, 'function', True, True),  # reuse = true, function
    ('false', 'true', 'false', 'false', False, 'module', True, True),  # reuse = true, module
    ('false', 'true', 'false', 'false', False, 'session', True, False),  # reuse = true, session
    # reuse_driver_from_tags
    ('false', 'false', 'false', 'false', True, 'function', True, True),  # reuse = true, function
    ('false', 'false', 'false', 'false', True, 'module', True, False),  # reuse = true, module
    ('false', 'false', 'false', 'false', True, 'session', True, False),  # reuse = true, session
)


@pytest.mark.parametrize("reuse_driver, reuse_driver_session, restart_driver_after_failure, restart_driver_fail, "
                         "reuse_driver_from_tags, scope, test_passed, expected_should_reuse_driver", should_be_reused)
def test_should_reuse_driver(reuse_driver, reuse_driver_session, restart_driver_after_failure, restart_driver_fail,
                             reuse_driver_from_tags, scope, test_passed, expected_should_reuse_driver, driver_wrapper):
    # Set config properties
    driver_wrapper.config.set('Driver', 'reuse_driver', reuse_driver)
    driver_wrapper.config.set('Driver', 'reuse_driver_session', reuse_driver_session)
    driver_wrapper.config.set('Driver', 'restart_driver_after_failure', restart_driver_after_failure)
    driver_wrapper.config.set('Driver', 'restart_driver_fail', restart_driver_fail)

    # Create context mock
    context = mock.MagicMock()
    context.reuse_driver_from_tags = reuse_driver_from_tags

    assert driver_wrapper.should_reuse_driver(scope, test_passed, context) == expected_should_reuse_driver
