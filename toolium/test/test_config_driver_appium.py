# -*- coding: utf-8 -*-
"""
Copyright 2023 Telefónica Investigación y Desarrollo, S.A.U.
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

import mock
import pytest
from appium.options.common.base import AppiumOptions

from toolium.config_driver import ConfigDriver
from toolium.config_parser import ExtendedConfigParser
from toolium.driver_wrappers_pool import DriverWrappersPool


DEFAULT_CAPABILITIES = {}


@pytest.fixture
def config():
    config_parser = ExtendedConfigParser()
    config_parser.add_section('Server')
    config_parser.add_section('Driver')
    return config_parser


@pytest.fixture
def utils():
    utils = mock.MagicMock()
    return utils


appium_driver_types = (
    'android',
    'ios',
    'iphone'
)


@mock.patch('toolium.config_driver.appiumdriver')
@pytest.mark.parametrize('driver_type', appium_driver_types)
def test_create_local_driver_appium(appiumdriver_mock, driver_type, config, utils):
    utils.get_driver_name.return_value = driver_type
    config.set('Driver', 'type', driver_type)
    config_driver = ConfigDriver(config, utils)
    config_driver._create_remote_driver = lambda: 'remote driver mock'

    driver = config_driver._create_local_driver()

    # Check that server has been configured and remote method has been called
    assert config.get('Server', 'host') == '127.0.0.1'
    assert config.get('Server', 'port') == '4723'
    assert driver == 'remote driver mock'


@mock.patch('toolium.config_driver.appiumdriver')
@pytest.mark.parametrize('driver_type', appium_driver_types)
def test_create_remote_driver_appium(appiumdriver_mock, driver_type, config, utils):
    utils.get_driver_name.return_value = driver_type
    config.set('Driver', 'type', driver_type)
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''
    expected_capabilities = DEFAULT_CAPABILITIES

    config_driver._create_remote_driver()

    # Check that appium options contain expected capabilities
    args, kwargs = appiumdriver_mock.Remote.call_args
    options = kwargs['options']
    assert isinstance(options, AppiumOptions)
    assert options.capabilities == expected_capabilities
    appiumdriver_mock.Remote.assert_called_once_with(command_executor=server_url, options=options)


@mock.patch('toolium.config_driver.appiumdriver')
@pytest.mark.parametrize('driver_type', appium_driver_types)
def test_create_remote_driver_appium_basepath(appiumdriver_mock, driver_type, config, utils):
    utils.get_driver_name.return_value = driver_type
    config.set('Driver', 'type', driver_type)
    config.set('Server', 'base_path', '/wd/hub')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''
    expected_capabilities = DEFAULT_CAPABILITIES

    config_driver._create_remote_driver()

    # Check that appium options contain expected capabilities
    args, kwargs = appiumdriver_mock.Remote.call_args
    options = kwargs['options']
    assert isinstance(options, AppiumOptions)
    assert options.capabilities == expected_capabilities
    appiumdriver_mock.Remote.assert_called_once_with(command_executor=f'{server_url}/wd/hub', options=options)


@mock.patch('toolium.config_driver.appiumdriver')
def test_create_remote_driver_android_capabilities(appiumdriver_mock, config, utils):
    driver_type = 'android'
    utils.get_driver_name.return_value = driver_type
    config.set('Driver', 'type', driver_type)
    config.add_section('Capabilities')
    config.set('Capabilities', 'platformName', 'Android')
    config.add_section('AppiumCapabilities')
    config.set('AppiumCapabilities', 'automationName', 'UiAutomator2')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''
    expected_capabilities = DEFAULT_CAPABILITIES
    expected_capabilities['platformName'] = 'Android'
    expected_capabilities['appium:automationName'] = 'UiAutomator2'

    config_driver._create_remote_driver()

    # Check that appium options contain expected capabilities
    args, kwargs = appiumdriver_mock.Remote.call_args
    options = kwargs['options']
    assert isinstance(options, AppiumOptions)
    assert options.capabilities == expected_capabilities
    appiumdriver_mock.Remote.assert_called_once_with(command_executor=server_url, options=options)


@mock.patch('toolium.config_driver.appiumdriver')
def test_create_remote_driver_ios_capabilities(appiumdriver_mock, config, utils):
    driver_type = 'ios'
    utils.get_driver_name.return_value = driver_type
    config.set('Driver', 'type', driver_type)
    config.add_section('Capabilities')
    config.set('Capabilities', 'platformName', 'iOS')
    config.add_section('AppiumCapabilities')
    config.set('AppiumCapabilities', 'automationName', 'XCUITest')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''
    expected_capabilities = DEFAULT_CAPABILITIES
    expected_capabilities['platformName'] = 'iOS'
    expected_capabilities['appium:automationName'] = 'XCUITest'

    config_driver._create_remote_driver()

    # Check that appium options contain expected capabilities
    args, kwargs = appiumdriver_mock.Remote.call_args
    options = kwargs['options']
    assert isinstance(options, AppiumOptions)
    assert options.capabilities == expected_capabilities
    appiumdriver_mock.Remote.assert_called_once_with(command_executor=server_url, options=options)
