# -*- coding: utf-8 -*-
"""
Copyright 2016 Telefónica Investigación y Desarrollo, S.A.U.
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

import pytest

from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool

environment_properties = []


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
    DriverWrappersPool.configure_common_directories(config_files)
    new_driver_wrapper.configure_logger()

    yield new_driver_wrapper

    # Remove used environment properties after test
    global environment_properties
    for env_property in environment_properties:
        try:
            del os.environ[env_property]
        except KeyError:
            pass
    environment_properties = []


def test_configure_properties(driver_wrapper):
    environment_properties.append('TOOLIUM_CONFIG_PROPERTIES_FILENAMES')
    os.environ['TOOLIUM_CONFIG_PROPERTIES_FILENAMES'] = 'properties.cfg'
    driver_wrapper.configure_properties()
    assert driver_wrapper.config.get('Driver', 'type') == 'firefox'  # get last value
    assert driver_wrapper.config.get_optional('Driver', 'implicitly_wait') == '5'  # only in properties
    assert driver_wrapper.config.get_optional('AppiumCapabilities', 'app') is None  # only in android


def test_configure_properties_android(driver_wrapper):
    environment_properties.append('TOOLIUM_CONFIG_PROPERTIES_FILENAMES')
    os.environ['TOOLIUM_CONFIG_PROPERTIES_FILENAMES'] = 'android-properties.cfg'
    driver_wrapper.configure_properties()
    assert driver_wrapper.config.get('Driver', 'type') == 'android'  # get last value
    assert driver_wrapper.config.get_optional('Driver', 'implicitly_wait') is None  # only in properties
    assert driver_wrapper.config.get_optional('AppiumCapabilities',
                                              'app') == 'http://invented_url/Demo.apk'  # only in android


def test_configure_properties_two_files(driver_wrapper):
    environment_properties.append('TOOLIUM_CONFIG_PROPERTIES_FILENAMES')
    os.environ['TOOLIUM_CONFIG_PROPERTIES_FILENAMES'] = 'properties.cfg;android-properties.cfg'
    driver_wrapper.configure_properties()
    assert driver_wrapper.config.get('Driver', 'type') == 'android'  # get last value
    assert driver_wrapper.config.get_optional('Driver', 'implicitly_wait') == '5'  # only in properties
    assert driver_wrapper.config.get_optional('AppiumCapabilities',
                                              'app') == 'http://invented_url/Demo.apk'  # only in android


def test_configure_properties_two_files_android_first(driver_wrapper):
    environment_properties.append('TOOLIUM_CONFIG_PROPERTIES_FILENAMES')
    os.environ['TOOLIUM_CONFIG_PROPERTIES_FILENAMES'] = 'android-properties.cfg;properties.cfg'
    driver_wrapper.configure_properties()
    assert driver_wrapper.config.get('Driver', 'type') == 'firefox'  # get last value
    assert driver_wrapper.config.get_optional('Driver', 'implicitly_wait') == '5'  # only in properties
    assert driver_wrapper.config.get_optional('AppiumCapabilities',
                                              'app') == 'http://invented_url/Demo.apk'  # only in android


def test_configure_properties_system_property(driver_wrapper):
    environment_properties.append('TOOLIUM_CONFIG_PROPERTIES_FILENAMES')
    environment_properties.append('TOOLIUM_DRIVER_TYPE')
    os.environ['TOOLIUM_CONFIG_PROPERTIES_FILENAMES'] = 'properties.cfg'
    os.environ['TOOLIUM_DRIVER_TYPE'] = 'Driver_type=edge'
    driver_wrapper.configure_properties()
    assert driver_wrapper.config.get('Driver', 'type') == 'edge'


def test_configure_properties_file_default_file(driver_wrapper):
    driver_wrapper.configure_properties()
    assert driver_wrapper.config.get('Driver', 'type') == 'firefox'


def test_configure_properties_file_not_found(driver_wrapper):
    environment_properties.append('TOOLIUM_CONFIG_PROPERTIES_FILENAMES')
    os.environ['TOOLIUM_CONFIG_PROPERTIES_FILENAMES'] = 'notfound-properties.cfg'
    with pytest.raises(Exception) as excinfo:
        driver_wrapper.configure_properties()
    assert 'Properties config file not found' in str(excinfo.value)


def test_configure_properties_no_changes(driver_wrapper):
    # Configure properties
    environment_properties.append('TOOLIUM_CONFIG_PROPERTIES_FILENAMES')
    os.environ['TOOLIUM_CONFIG_PROPERTIES_FILENAMES'] = 'properties.cfg'
    driver_wrapper.configure_properties()
    assert driver_wrapper.config.get('Driver', 'type') == 'firefox'

    # Modify property
    new_driver_type = 'edge'
    driver_wrapper.config.set('Driver', 'type', new_driver_type)
    assert driver_wrapper.config.get('Driver', 'type') == new_driver_type

    # Trying to configure again
    driver_wrapper.configure_properties()

    # Configuration has not been initialized
    assert driver_wrapper.config.get('Driver', 'type') == new_driver_type


def test_configure_properties_change_configuration_file(driver_wrapper):
    # Configure properties
    environment_properties.append('TOOLIUM_CONFIG_PROPERTIES_FILENAMES')
    os.environ['TOOLIUM_CONFIG_PROPERTIES_FILENAMES'] = 'properties.cfg'
    driver_wrapper.configure_properties()
    assert driver_wrapper.config.get('Driver', 'type') == 'firefox'

    # Modify property
    new_driver_type = 'edge'
    driver_wrapper.config.set('Driver', 'type', new_driver_type)
    assert driver_wrapper.config.get('Driver', 'type') == new_driver_type

    # Change file and try to configure again
    environment_properties.append('TOOLIUM_CONFIG_PROPERTIES_FILENAMES')
    os.environ['TOOLIUM_CONFIG_PROPERTIES_FILENAMES'] = 'android-properties.cfg'
    driver_wrapper.configure_properties()

    # Check that configuration has been initialized
    assert driver_wrapper.config.get('Driver', 'type') == 'android'


def test_configure_properties_finalize_properties(driver_wrapper):
    environment_properties.append('TOOLIUM_CONFIG_PROPERTIES_FILENAMES')
    environment_properties.append('TOOLIUM_DRIVER_TYPE')
    os.environ['TOOLIUM_CONFIG_PROPERTIES_FILENAMES'] = 'properties.cfg'
    os.environ['TOOLIUM_DRIVER_TYPE'] = 'Driver_type=edge'

    # Modify properties after reading properties file and system properties
    def finalize_properties_configuration(self):
        self.config.set('Driver', 'type', 'chrome')

    original_method = DriverWrapper.finalize_properties_configuration
    DriverWrapper.finalize_properties_configuration = finalize_properties_configuration

    driver_wrapper.configure_properties()
    # properties file: firefox
    # system property: edge
    # finalize properties method: chrome
    assert driver_wrapper.config.get('Driver', 'type') == 'chrome'

    # Restore monkey patching after test
    DriverWrapper.finalize_properties_configuration = original_method
