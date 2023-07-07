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
from selenium.webdriver.chrome.options import Options

from toolium.config_driver import ConfigDriver
from toolium.config_parser import ExtendedConfigParser


DEFAULT_CAPABILITIES = {'browserName': 'chrome', 'pageLoadStrategy': 'normal'}


@pytest.fixture
def config():
    config_parser = ExtendedConfigParser()
    config_parser.add_section('Server')
    config_parser.add_section('Driver')
    return config_parser


@pytest.fixture
def utils():
    utils = mock.MagicMock()
    utils.get_driver_name.return_value = 'chrome'
    return utils


@mock.patch('toolium.config_driver.ChromeOptions')
@mock.patch('toolium.config_driver.ChromeService')
@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_chrome_no_driver_path(webdriver_mock, service, options, config, utils):
    config.set('Driver', 'type', 'chrome')
    config_driver = ConfigDriver(config, utils)

    config_driver._create_local_driver()
    service.assert_called_once_with()
    options.assert_called_once_with()
    webdriver_mock.Chrome.assert_called_once_with(service=service(), options=options())


@mock.patch('toolium.config_driver.ChromeOptions')
@mock.patch('toolium.config_driver.ChromeService')
@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_chrome_driver_path(webdriver_mock, service, options, config, utils):
    config.set('Driver', 'type', 'chrome')
    config.set('Driver', 'chrome_driver_path', '/tmp/driver')
    config_driver = ConfigDriver(config, utils)

    config_driver._create_local_driver()
    service.assert_called_once_with(executable_path='/tmp/driver')
    options.assert_called_once_with()
    webdriver_mock.Chrome.assert_called_once_with(service=service(), options=options())


def test_get_chrome_options(config, utils):
    config_driver = ConfigDriver(config, utils)
    expected_arguments = []
    expected_capabilities = DEFAULT_CAPABILITIES
    expected_experimental_options = {}
    expected_extensions_len = 0
    expected_binary_location = ''

    options = config_driver._get_chrome_options()

    assert options.arguments == expected_arguments
    assert options.capabilities == expected_capabilities
    assert options.experimental_options == expected_experimental_options
    assert len(options.extensions) == expected_extensions_len
    assert options.binary_location == expected_binary_location


def test_get_chrome_options_multiple_options(config, utils):
    config.add_section('ChromePreferences')
    config.set('ChromePreferences', 'download.default_directory', '/tmp')
    config.add_section('ChromeMobileEmulation')
    config.set('ChromeMobileEmulation', 'deviceName', 'Google Nexus 5')
    config.add_section('ChromeArguments')
    config.set('ChromeArguments', 'lang', 'es')
    config.add_section('ChromeExtensions')
    config.set('ChromeExtensions', 'extension_name', 'toolium/test/resources/extension.crx')
    config_driver = ConfigDriver(config, utils)
    expected_arguments = ['lang=es']
    expected_capabilities = DEFAULT_CAPABILITIES
    expected_experimental_options = {
        'prefs': {'download.default_directory': '/tmp'},
        'mobileEmulation': {'deviceName': 'Google Nexus 5'}
    }
    expected_extensions_len = 1
    expected_binary_location = ''

    options = config_driver._get_chrome_options()

    assert options.arguments == expected_arguments
    assert options.capabilities == expected_capabilities
    assert options.experimental_options == expected_experimental_options
    assert len(options.extensions) == expected_extensions_len
    assert options.binary_location == expected_binary_location


def test_get_chrome_options_binary(config, utils):
    config.add_section('Chrome')
    config.set('Chrome', 'binary', '/tmp/chrome')
    config_driver = ConfigDriver(config, utils)
    expected_arguments = []
    expected_capabilities = DEFAULT_CAPABILITIES
    expected_experimental_options = {}
    expected_extensions_len = 0
    expected_binary_location = '/tmp/chrome'

    options = config_driver._get_chrome_options()

    assert options.arguments == expected_arguments
    assert options.capabilities == expected_capabilities
    assert options.experimental_options == expected_experimental_options
    assert len(options.extensions) == expected_extensions_len
    assert options.binary_location == expected_binary_location


def test_get_chrome_options_additional(config, utils):
    config.add_section('Chrome')
    config.set('Chrome', 'options',
               "{'excludeSwitches': ['enable-automation'], 'perfLoggingPrefs': {'enableNetwork': True}}")
    config_driver = ConfigDriver(config, utils)
    expected_arguments = []
    expected_capabilities = DEFAULT_CAPABILITIES
    expected_experimental_options = {
        'excludeSwitches': ['enable-automation'],
        'perfLoggingPrefs': {'enableNetwork': True}
    }
    expected_extensions_len = 0
    expected_binary_location = ''

    options = config_driver._get_chrome_options()

    assert options.arguments == expected_arguments
    assert options.capabilities == expected_capabilities
    assert options.experimental_options == expected_experimental_options
    assert len(options.extensions) == expected_extensions_len
    assert options.binary_location == expected_binary_location


def test_get_chrome_options_headless(config, utils):
    config.set('Driver', 'headless', 'true')
    config_driver = ConfigDriver(config, utils)
    expected_arguments = ['--headless=new']
    expected_capabilities = DEFAULT_CAPABILITIES
    expected_experimental_options = {}
    expected_extensions_len = 0
    expected_binary_location = ''

    options = config_driver._get_chrome_options()

    assert options.arguments == expected_arguments
    assert options.capabilities == expected_capabilities
    assert options.experimental_options == expected_experimental_options
    assert len(options.extensions) == expected_extensions_len
    assert options.binary_location == expected_binary_location


def test_get_chrome_options_capabilities_new(config, utils):
    config.add_section('Capabilities')
    config.set('Capabilities', 'pageLoadStrategy', 'eager')
    config_driver = ConfigDriver(config, utils)
    expected_arguments = []
    expected_capabilities = DEFAULT_CAPABILITIES.copy()
    expected_capabilities['pageLoadStrategy'] = 'eager'
    expected_experimental_options = {}
    expected_extensions_len = 0
    expected_binary_location = ''

    options = config_driver._get_chrome_options()

    assert options.arguments == expected_arguments
    assert options.capabilities == expected_capabilities
    assert options.experimental_options == expected_experimental_options
    assert len(options.extensions) == expected_extensions_len
    assert options.binary_location == expected_binary_location


def test_get_chrome_options_capabilities_update(config, utils):
    config.add_section('Capabilities')
    config.set('Capabilities', 'browserVersion', '50')
    config.set('Capabilities', 'platformVersion', '14')
    # TODO: next line it should not be needed, but config object has not been cleaned after previous test
    config.set('Capabilities', 'pageLoadStrategy', 'normal')
    config_driver = ConfigDriver(config, utils)
    expected_arguments = []
    expected_capabilities = DEFAULT_CAPABILITIES.copy()
    # browserVersion and platformVersion are not converted to int
    expected_capabilities['browserVersion'] = '50'
    expected_capabilities['platformVersion'] = '14'
    expected_experimental_options = {}
    expected_extensions_len = 0
    expected_binary_location = ''

    options = config_driver._get_chrome_options()

    assert options.arguments == expected_arguments
    assert options.capabilities == expected_capabilities
    assert options.experimental_options == expected_experimental_options
    assert len(options.extensions) == expected_extensions_len
    assert options.binary_location == expected_binary_location


def test_get_chrome_options_with_previous_capabilities(config, utils):
    config_driver = ConfigDriver(config, utils)
    expected_arguments = []
    expected_capabilities = DEFAULT_CAPABILITIES.copy()
    expected_capabilities['browserVersion'] = '100'
    expected_experimental_options = {}
    expected_extensions_len = 0
    expected_binary_location = ''

    previous_capabilities = {'browserVersion': '100'}
    options = config_driver._get_chrome_options(previous_capabilities)

    assert options.arguments == expected_arguments
    assert options.capabilities == expected_capabilities
    assert options.experimental_options == expected_experimental_options
    assert len(options.extensions) == expected_extensions_len
    assert options.binary_location == expected_binary_location


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_chrome(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'chrome')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    config_driver = ConfigDriver(config, utils)
    expected_capabilities = DEFAULT_CAPABILITIES

    config_driver._create_remote_driver()

    # Check that chrome options contain expected capabilities
    args, kwargs = webdriver_mock.Remote.call_args
    options = kwargs['options']
    assert isinstance(options, Options)
    assert options.capabilities == expected_capabilities
    webdriver_mock.Remote.assert_called_once_with(command_executor=server_url, options=options)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_chrome_basepath(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'chrome')
    config.set('Server', 'base_path', '/wd/hub')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    config_driver = ConfigDriver(config, utils)
    expected_capabilities = DEFAULT_CAPABILITIES

    config_driver._create_remote_driver()

    # Check that chrome options contain expected capabilities
    args, kwargs = webdriver_mock.Remote.call_args
    options = kwargs['options']
    assert isinstance(options, Options)
    assert options.capabilities == expected_capabilities
    webdriver_mock.Remote.assert_called_once_with(command_executor=f'{server_url}/wd/hub', options=options)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_chrome_with_version_and_platform(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'chrome-latest-on-windows')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    config_driver = ConfigDriver(config, utils)
    expected_capabilities = DEFAULT_CAPABILITIES.copy()
    expected_capabilities['browserVersion'] = 'latest'
    expected_capabilities['platformName'] = 'windows'

    config_driver._create_remote_driver()

    # Check that chrome options contain expected capabilities
    args, kwargs = webdriver_mock.Remote.call_args
    options = kwargs['options']
    assert isinstance(options, Options)
    assert options.capabilities == expected_capabilities
    webdriver_mock.Remote.assert_called_once_with(command_executor=server_url, options=options)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_chrome_with_version_and_platform_uppercase(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'chrome-latest-on-WINDOWS')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    config_driver = ConfigDriver(config, utils)
    expected_capabilities = DEFAULT_CAPABILITIES.copy()
    expected_capabilities['browserVersion'] = 'latest'
    expected_capabilities['platformName'] = 'windows'

    config_driver._create_remote_driver()

    # Check that chrome options contain expected capabilities
    args, kwargs = webdriver_mock.Remote.call_args
    options = kwargs['options']
    assert isinstance(options, Options)
    assert options.capabilities == expected_capabilities
    webdriver_mock.Remote.assert_called_once_with(command_executor=server_url, options=options)
