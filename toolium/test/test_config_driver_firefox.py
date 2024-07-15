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
from selenium.webdriver.firefox.options import Options

from toolium.config_driver import ConfigDriver
from toolium.config_parser import ExtendedConfigParser
from toolium.driver_wrappers_pool import DriverWrappersPool


DEFAULT_CAPABILITIES = {'acceptInsecureCerts': True, 'browserName': 'firefox', 'moz:debuggerAddress': True,
                        'pageLoadStrategy': 'normal'}
DEFAULT_PREFERENCES = {'remote.active-protocols': 3}


@pytest.fixture
def config():
    config_parser = ExtendedConfigParser()
    config_parser.add_section('Server')
    config_parser.add_section('Driver')
    return config_parser


@pytest.fixture
def utils():
    utils = mock.MagicMock()
    utils.get_driver_name.return_value = 'firefox'
    return utils


@mock.patch('toolium.config_driver.FirefoxOptions')
@mock.patch('toolium.config_driver.FirefoxService')
@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_firefox_no_driver_path(webdriver_mock, service, options, config, utils):
    config.set('Driver', 'type', 'firefox')
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''

    config_driver._create_local_driver()
    service.assert_called_once_with(log_path='geckodriver.log')
    options.assert_called_once_with()
    webdriver_mock.Firefox.assert_called_once_with(service=service(), options=options())


@mock.patch('toolium.config_driver.FirefoxOptions')
@mock.patch('toolium.config_driver.FirefoxService')
@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_firefox_driver_path(webdriver_mock, service, options, config, utils):
    config.set('Driver', 'type', 'firefox')
    config.set('Driver', 'gecko_driver_path', '/tmp/driver')
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''

    config_driver._create_local_driver()

    service.assert_called_once_with(executable_path='/tmp/driver', log_path='geckodriver.log')
    webdriver_mock.Firefox.assert_called_once_with(service=service(), options=options())


@mock.patch('toolium.config_driver.FirefoxService')
@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_firefox_headless(webdriver_mock, service, config, utils):
    config.set('Driver', 'type', 'firefox')
    config.set('Driver', 'headless', 'true')
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''

    config_driver._create_local_driver()

    # Check that firefox options contain the headless option
    service.assert_called_once_with(log_path='geckodriver.log')
    args, kwargs = webdriver_mock.Firefox.call_args
    options = kwargs['options']
    assert isinstance(options, Options)
    assert options.arguments == ['-headless']
    webdriver_mock.Firefox.assert_called_once_with(service=service(), options=options)


@mock.patch('toolium.config_driver.FirefoxService')
@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_firefox_binary(webdriver_mock, service, config, utils):
    config.set('Driver', 'type', 'firefox')
    config.add_section('Firefox')
    config.set('Firefox', 'binary', '/tmp/firefox')
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''

    config_driver._create_local_driver()

    # Check that firefox options contain the firefox binary
    service.assert_called_once_with(log_path='geckodriver.log')
    args, kwargs = webdriver_mock.Firefox.call_args
    options = kwargs['options']
    assert isinstance(options, Options)
    assert options.binary._start_cmd == '/tmp/firefox'
    webdriver_mock.Firefox.assert_called_once_with(service=service(), options=options)


@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_firefox_extension(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'firefox')
    config.add_section('FirefoxExtensions')
    config.set('FirefoxExtensions', 'firebug', 'resources/firebug-3.0.0-beta.3.xpi')
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''

    config_driver._create_local_driver()

    # Check that extension has been added to driver
    webdriver_mock.Firefox.install_addon.assert_called_once_with(webdriver_mock.Firefox(),
                                                                 'resources/firebug-3.0.0-beta.3.xpi', temporary=True)


def test_get_firefox_options(config, utils):
    config_driver = ConfigDriver(config, utils)
    expected_arguments = []
    expected_preferences = DEFAULT_PREFERENCES
    expected_capabilities = DEFAULT_CAPABILITIES

    options = config_driver._get_firefox_options()

    assert options.arguments == expected_arguments
    assert options.preferences == expected_preferences
    assert options.capabilities == expected_capabilities


def test_get_firefox_options_arguments(config, utils):
    config.add_section('FirefoxArguments')
    config.set('FirefoxArguments', '-private', '')
    config_driver = ConfigDriver(config, utils)
    expected_arguments = ['-private']
    expected_preferences = DEFAULT_PREFERENCES
    expected_capabilities = DEFAULT_CAPABILITIES

    options = config_driver._get_firefox_options()

    assert options.arguments == expected_arguments
    assert options.preferences == expected_preferences
    assert options.capabilities == expected_capabilities


def test_get_firefox_options_preferences(config, utils):
    config.add_section('FirefoxPreferences')
    config.set('FirefoxPreferences', 'browser.download.folderList', '2')
    config_driver = ConfigDriver(config, utils)
    expected_arguments = []
    expected_preferences = DEFAULT_PREFERENCES.copy()
    expected_preferences['browser.download.folderList'] = 2
    expected_capabilities = DEFAULT_CAPABILITIES

    options = config_driver._get_firefox_options()

    assert options.arguments == expected_arguments
    assert options.preferences == expected_preferences
    assert options.capabilities == expected_capabilities


def test_get_firefox_options_profile(config, utils):
    config.add_section('Firefox')
    config.set('Firefox', 'profile', '/tmp')
    config_driver = ConfigDriver(config, utils)
    expected_arguments = []
    expected_preferences = DEFAULT_PREFERENCES.copy()
    expected_preferences['profile'] = '/tmp'
    expected_capabilities = DEFAULT_CAPABILITIES

    options = config_driver._get_firefox_options()

    assert options.arguments == expected_arguments
    assert options.preferences == expected_preferences
    assert options.capabilities == expected_capabilities


def test_get_firefox_options_capabilities_update(config, utils):
    config.add_section('Capabilities')
    config.set('Capabilities', 'pageLoadStrategy', 'eager')
    config_driver = ConfigDriver(config, utils)
    expected_arguments = []
    expected_preferences = DEFAULT_PREFERENCES
    expected_capabilities = DEFAULT_CAPABILITIES.copy()
    expected_capabilities['pageLoadStrategy'] = 'eager'

    options = config_driver._get_firefox_options()

    assert options.arguments == expected_arguments
    assert options.preferences == expected_preferences
    assert options.capabilities == expected_capabilities


def test_get_firefox_options_capabilities_new(config, utils):
    config.add_section('Capabilities')
    config.set('Capabilities', 'browserVersion', '50')
    # TODO: next line it should not be needed, but config object has not been cleaned after previous test
    config.set('Capabilities', 'pageLoadStrategy', 'normal')
    config_driver = ConfigDriver(config, utils)
    expected_arguments = []
    expected_preferences = DEFAULT_PREFERENCES
    expected_capabilities = DEFAULT_CAPABILITIES.copy()
    expected_capabilities['browserVersion'] = '50'

    options = config_driver._get_firefox_options()

    assert options.arguments == expected_arguments
    assert options.preferences == expected_preferences
    assert options.capabilities == expected_capabilities


def test_get_firefox_options_with_previous_capabilities(config, utils):
    config_driver = ConfigDriver(config, utils)
    expected_arguments = []
    expected_preferences = DEFAULT_PREFERENCES
    expected_capabilities = DEFAULT_CAPABILITIES.copy()
    expected_capabilities['browserVersion'] = '100'

    previous_capabilities = {'browserVersion': '100'}
    options = config_driver._get_firefox_options(previous_capabilities)

    assert options.arguments == expected_arguments
    assert options.preferences == expected_preferences
    assert options.capabilities == expected_capabilities


def test_add_firefox_arguments(config, utils):
    config.add_section('FirefoxArguments')
    config.set('FirefoxArguments', '-private', '')
    config_driver = ConfigDriver(config, utils)
    options = Options()

    config_driver._add_firefox_arguments(options)
    assert options.arguments == ['-private']


def test_add_firefox_arguments_no_section(config, utils):
    config_driver = ConfigDriver(config, utils)
    options = Options()

    config_driver._add_firefox_arguments(options)
    assert options.arguments == []


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_firefox(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'firefox')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''
    expected_capabilities = DEFAULT_CAPABILITIES

    config_driver._create_remote_driver()

    # Check that firefox options contain expected capabilities
    args, kwargs = webdriver_mock.Remote.call_args
    options = kwargs['options']
    assert isinstance(options, Options)
    assert options.capabilities == expected_capabilities
    webdriver_mock.Remote.assert_called_once_with(command_executor=server_url, options=options)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_firefox_basepath(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'firefox')
    config.set('Server', 'base_path', '/wd/hub')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''
    expected_capabilities = DEFAULT_CAPABILITIES

    config_driver._create_remote_driver()

    # Check that firefox options contain expected capabilities
    args, kwargs = webdriver_mock.Remote.call_args
    options = kwargs['options']
    assert isinstance(options, Options)
    assert options.capabilities == expected_capabilities
    webdriver_mock.Remote.assert_called_once_with(command_executor=f'{server_url}/wd/hub', options=options)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_firefox_with_version_and_platform(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'firefox-50-on-linux')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''
    expected_capabilities = DEFAULT_CAPABILITIES.copy()
    expected_capabilities['browserVersion'] = '50'
    expected_capabilities['platformName'] = 'linux'

    config_driver._create_remote_driver()

    # Check that firefox options contain expected capabilities
    args, kwargs = webdriver_mock.Remote.call_args
    options = kwargs['options']
    assert isinstance(options, Options)
    assert options.capabilities == expected_capabilities
    webdriver_mock.Remote.assert_called_once_with(command_executor=server_url, options=options)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_firefox_with_version_and_platform_uppercase(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'firefox-50-on-LINUX')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''
    expected_capabilities = DEFAULT_CAPABILITIES.copy()
    expected_capabilities['browserVersion'] = '50'
    expected_capabilities['platformName'] = 'linux'

    config_driver._create_remote_driver()

    # Check that firefox options contain expected capabilities
    args, kwargs = webdriver_mock.Remote.call_args
    options = kwargs['options']
    assert isinstance(options, Options)
    assert options.capabilities == expected_capabilities
    webdriver_mock.Remote.assert_called_once_with(command_executor=server_url, options=options)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_firefox_extension(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'firefox')
    config.add_section('FirefoxExtensions')
    config.set('FirefoxExtensions', 'firebug', 'resources/firebug-3.0.0-beta.3.xpi')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''
    expected_capabilities = DEFAULT_CAPABILITIES

    config_driver._create_remote_driver()

    # Check that firefox options contain expected capabilities
    args, kwargs = webdriver_mock.Remote.call_args
    options = kwargs['options']
    assert isinstance(options, Options)
    assert options.capabilities == expected_capabilities
    webdriver_mock.Remote.assert_called_once_with(command_executor=server_url, options=options)

    # Check that extension has been added to driver
    webdriver_mock.Firefox.install_addon.assert_called_once_with(webdriver_mock.Remote(),
                                                                 'resources/firebug-3.0.0-beta.3.xpi', temporary=True)
