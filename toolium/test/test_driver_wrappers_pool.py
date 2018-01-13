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

import os

import mock
import pytest

from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool


@pytest.fixture
def driver_wrapper():
    # Reset wrappers pool values
    DriverWrappersPool._empty_pool()

    # Create default wrapper
    driver_wrapper = DriverWrappersPool.get_default_wrapper()

    # Configure properties
    config_files = ConfigFiles()
    root_path = os.path.dirname(os.path.realpath(__file__))
    config_files.set_config_directory(os.path.join(root_path, 'conf'))
    config_files.set_output_directory(os.path.join(root_path, 'output'))
    driver_wrapper.configure(config_files)

    return driver_wrapper


def test_singleton(driver_wrapper):
    # Request default wrapper
    new_wrapper = DriverWrappersPool.get_default_wrapper()

    # Modify new wrapper
    new_driver_type = 'opera'
    new_wrapper.config.set('Driver', 'type', new_driver_type)

    # Check that both wrappers are the same object
    assert new_driver_type == driver_wrapper.config.get('Driver', 'type')
    assert new_driver_type == new_wrapper.config.get('Driver', 'type')
    assert driver_wrapper == new_wrapper
    assert DriverWrappersPool.driver_wrappers[0] == driver_wrapper


def test_multiple(driver_wrapper):
    # Request a new additional wrapper
    new_wrapper = DriverWrapper()

    # Check that wrapper and new_wrapper are different
    assert driver_wrapper != new_wrapper
    assert DriverWrappersPool.driver_wrappers[0] == driver_wrapper
    assert DriverWrappersPool.driver_wrappers[1] == new_wrapper


def test_connect_default_driver_wrapper(driver_wrapper):
    driver_wrapper.connect = mock.MagicMock()

    # Connect default driver wrapper
    new_wrapper = DriverWrappersPool.connect_default_driver_wrapper()

    # Check that both wrappers are the same object and connect has been called
    assert new_wrapper == driver_wrapper
    driver_wrapper.connect.assert_called_once_with()


def test_connect_default_driver_wrapper_already_connected(driver_wrapper):
    driver_wrapper.connect = mock.MagicMock()
    driver_wrapper.driver = 'fake'

    # Connect default driver wrapper
    new_wrapper = DriverWrappersPool.connect_default_driver_wrapper()

    # Check that both wrappers are the same object and connect has not been called
    assert new_wrapper == driver_wrapper
    driver_wrapper.connect.assert_not_called()


close_drivers_scopes = (
    'function',
    'module',
    'session',
)


@pytest.mark.parametrize("scope", close_drivers_scopes)
def test_close_drivers_function(scope, driver_wrapper):
    DriverWrappersPool.save_all_webdriver_logs = mock.MagicMock()

    # Close drivers
    DriverWrappersPool.close_drivers(scope, 'test_name')

    if scope == 'function':
        # Check that save_all_webdriver_logs has been called
        DriverWrappersPool.save_all_webdriver_logs.assert_called_once_with('test_name', True)
    else:
        # Check that save_all_webdriver_logs has not been called
        DriverWrappersPool.save_all_webdriver_logs.assert_not_called()


def test_find_parent_directory_relative():
    directory = 'conf'
    filename = 'properties.cfg'
    expected_config_directory = os.path.join(os.getcwd(), 'conf')

    assert expected_config_directory == DriverWrappersPool._find_parent_directory(directory, filename)


def test_find_parent_directory_file_not_found():
    directory = 'conf'
    filename = 'unknown'
    expected_config_directory = os.path.join(os.getcwd(), 'conf')

    assert expected_config_directory == DriverWrappersPool._find_parent_directory(directory, filename)


def test_find_parent_directory_absolute():
    directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'conf')
    filename = 'properties.cfg'
    expected_config_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'conf')

    assert expected_config_directory == DriverWrappersPool._find_parent_directory(directory, filename)


def test_find_parent_directory_absolute_recursively():
    directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'unknown', 'conf')
    filename = 'properties.cfg'
    expected_config_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'conf')

    assert expected_config_directory == DriverWrappersPool._find_parent_directory(directory, filename)


def test_initialize_config_files_new():
    config_files = None

    # Initialize config files
    init_config_files = DriverWrappersPool.initialize_config_files(config_files)

    # Check expected config files
    assert init_config_files.config_properties_filenames is None
    assert init_config_files.output_log_filename is None


def test_initialize_config_files_new_environment():
    config_files = None
    os.environ["Config_environment"] = 'android'

    # Initialize config files
    config_files = DriverWrappersPool.initialize_config_files(config_files)
    del os.environ["Config_environment"]

    # Check expected config files
    expected_properties_filenames = 'properties.cfg;android-properties.cfg;local-android-properties.cfg'
    assert config_files.config_properties_filenames == expected_properties_filenames
    assert config_files.output_log_filename == 'toolium_android.log'


def test_initialize_config_files_configured():
    config_files = ConfigFiles()
    config_files.set_config_properties_filenames('test.conf', 'local-test.conf')
    config_files.set_output_log_filename('test.log')

    # Initialize config files
    config_files = DriverWrappersPool.initialize_config_files(config_files)

    # Check expected config files
    assert config_files.config_properties_filenames == 'test.conf;local-test.conf'
    assert config_files.output_log_filename == 'test.log'


def test_initialize_config_files_configured_environment():
    config_files = ConfigFiles()
    config_files.set_config_properties_filenames('test.conf', 'local-test.conf')
    config_files.set_output_log_filename('test.log')
    os.environ["Config_environment"] = 'android'

    # Initialize config files
    config_files = DriverWrappersPool.initialize_config_files(config_files)
    del os.environ["Config_environment"]

    # Check expected config files
    expected_properties_filenames = 'test.conf;local-test.conf;android-test.conf;local-android-test.conf'
    assert config_files.config_properties_filenames == expected_properties_filenames
    assert config_files.output_log_filename == 'test_android.log'


def test_initialize_config_files_configured_environment_with_points():
    config_files = ConfigFiles()
    config_files.set_config_properties_filenames('test.new.conf', 'local-test.new.conf')
    config_files.set_output_log_filename('test.new.log')
    os.environ["Config_environment"] = 'ios'

    # Initialize config files
    config_files = DriverWrappersPool.initialize_config_files(config_files)
    del os.environ["Config_environment"]

    # Check expected config files
    expected_properties_filenames = 'test.new.conf;local-test.new.conf;ios-test.new.conf;local-ios-test.new.conf'
    assert config_files.config_properties_filenames == expected_properties_filenames
    assert config_files.output_log_filename == 'test.new_ios.log'
