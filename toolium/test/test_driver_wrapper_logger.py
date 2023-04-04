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

import logging
import os

import pytest

from toolium.config_files import ConfigFiles
from toolium.driver_wrappers_pool import DriverWrappersPool

environment_properties = []


@pytest.fixture
def driver_wrapper():
    # Create a new wrapper
    new_driver_wrapper = DriverWrappersPool.get_default_wrapper()

    # Configure wrapper
    config_files = ConfigFiles()
    root_path = os.path.dirname(os.path.realpath(__file__))
    config_files.set_config_directory(os.path.join(root_path, 'conf'))
    config_files.set_output_directory(os.path.join(root_path, 'output'))
    DriverWrappersPool.configure_common_directories(config_files)

    yield new_driver_wrapper

    # Remove used environment properties after test
    global environment_properties
    for env_property in environment_properties:
        try:
            del os.environ[env_property]
        except KeyError:
            pass
    environment_properties = []


def test_configure_logger(driver_wrapper):
    environment_properties.append('TOOLIUM_CONFIG_LOG_FILENAME')
    os.environ['TOOLIUM_CONFIG_LOG_FILENAME'] = 'logging.conf'
    driver_wrapper.configure_logger()
    assert logging.getLevelName(driver_wrapper.logger.getEffectiveLevel()) == 'DEBUG'


def test_configure_logger_file_not_configured(driver_wrapper):
    driver_wrapper.configure_logger()
    driver_wrapper.logger.info('No error, default logging configuration')


def test_configure_logger_file_not_found(driver_wrapper):
    environment_properties.append('TOOLIUM_CONFIG_LOG_FILENAME')
    os.environ['TOOLIUM_CONFIG_LOG_FILENAME'] = 'notfound-logging.conf'
    driver_wrapper.configure_logger()
    driver_wrapper.logger.info('No error, default logging configuration')


def test_configure_logger_no_changes(driver_wrapper):
    # Configure logger
    environment_properties.append('TOOLIUM_CONFIG_LOG_FILENAME')
    os.environ['TOOLIUM_CONFIG_LOG_FILENAME'] = 'logging.conf'
    driver_wrapper.configure_logger()
    logger = logging.getLogger('selenium.webdriver.remote.remote_connection')

    # Modify property
    new_level = 'INFO'
    logger.setLevel(new_level)
    assert logging.getLevelName(logger.level) == new_level

    # Trying to configure again
    driver_wrapper.configure_logger()

    # Configuration has not been initialized
    assert logging.getLevelName(logger.level) == new_level


def test_configure_logger_change_configuration_file(driver_wrapper):
    # Configure logger
    environment_properties.append('TOOLIUM_CONFIG_LOG_FILENAME')
    os.environ['TOOLIUM_CONFIG_LOG_FILENAME'] = 'logging.conf'
    logger = logging.getLogger('selenium.webdriver.remote.remote_connection')

    # Modify property
    new_level = 'INFO'
    logger.setLevel(new_level)
    assert logging.getLevelName(logger.level) == new_level

    # Change file and try to configure again
    os.environ['TOOLIUM_CONFIG_LOG_FILENAME'] = 'warn-logging.conf'
    driver_wrapper.configure_logger()

    # Check that configuration has been initialized
    assert logging.getLevelName(logger.level) == 'WARNING'
