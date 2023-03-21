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

import mock
import pytest
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from toolium.config_driver import ConfigDriver
from toolium.config_parser import ExtendedConfigParser
from toolium.driver_wrappers_pool import DriverWrappersPool


DEFAULT_CAPABILITIES = {'acceptInsecureCerts': True, 'browserName': 'firefox', 'moz:debuggerAddress': True,
                        'pageLoadStrategy': 'normal'}


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
def test_create_local_driver_firefox_no_gecko_path(webdriver_mock, service, options, config, utils):
    config.set('Driver', 'type', 'firefox')
    utils.get_driver_name.return_value = 'firefox'
    config_driver = ConfigDriver(config, utils)
    expected_profile = webdriver.FirefoxProfile()
    config_driver._create_firefox_profile = mock.MagicMock(return_value=expected_profile)
    DriverWrappersPool.output_directory = ''

    config_driver._create_local_driver()
    service.assert_called_once_with(log_path='geckodriver.log')
    options.assert_called_once_with()
    webdriver_mock.Firefox.assert_called_once_with(service=service(), options=options())


@mock.patch('toolium.config_driver.FirefoxOptions')
@mock.patch('toolium.config_driver.FirefoxService')
@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_firefox_gecko_path(webdriver_mock, service, options, config, utils):
    config.set('Driver', 'type', 'firefox')
    config.set('Driver', 'gecko_driver_path', '/tmp/driver')
    utils.get_driver_name.return_value = 'firefox'
    config_driver = ConfigDriver(config, utils)
    expected_profile = webdriver.FirefoxProfile()
    config_driver._create_firefox_profile = mock.MagicMock(return_value=expected_profile)
    DriverWrappersPool.output_directory = ''

    config_driver._create_local_driver()

    service.assert_called_once_with(executable_path='/tmp/driver', log_path='geckodriver.log')
    webdriver_mock.Firefox.assert_called_once_with(service=service(), options=options())


@mock.patch('toolium.config_driver.FirefoxService')
@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_firefox_headless(webdriver_mock, service, config, utils):
    config.set('Driver', 'type', 'firefox')
    config.set('Driver', 'headless', 'true')
    utils.get_driver_name.return_value = 'firefox'
    config_driver = ConfigDriver(config, utils)
    expected_profile = webdriver.FirefoxProfile()
    config_driver._create_firefox_profile = mock.MagicMock(return_value=expected_profile)
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
    utils.get_driver_name.return_value = 'firefox'
    config_driver = ConfigDriver(config, utils)
    expected_profile = webdriver.FirefoxProfile()
    config_driver._create_firefox_profile = mock.MagicMock(return_value=expected_profile)
    DriverWrappersPool.output_directory = ''

    config_driver._create_local_driver()

    # Check that firefox options contain the firefox binary
    service.assert_called_once_with(log_path='geckodriver.log')
    args, kwargs = webdriver_mock.Firefox.call_args
    options = kwargs['options']
    assert isinstance(options, Options)
    assert options.binary._start_cmd == '/tmp/firefox'
    webdriver_mock.Firefox.assert_called_once_with(service=service(), options=options)


def test_get_firefox_options(config, utils):
    config_driver = ConfigDriver(config, utils)
    expected_profile = webdriver.FirefoxProfile()
    config_driver._create_firefox_profile = mock.MagicMock(return_value=expected_profile)
    expected_arguments = []
    expected_capabilities = DEFAULT_CAPABILITIES

    firefox_options = config_driver._get_firefox_options()

    assert firefox_options.arguments == expected_arguments
    assert firefox_options.capabilities == expected_capabilities
    assert firefox_options.profile == expected_profile


def test_get_firefox_options_arguments(config, utils):
    config.add_section('FirefoxArguments')
    config.set('FirefoxArguments', '-private', '')
    config_driver = ConfigDriver(config, utils)
    expected_profile = webdriver.FirefoxProfile()
    config_driver._create_firefox_profile = mock.MagicMock(return_value=expected_profile)
    expected_arguments = ['-private']
    expected_capabilities = DEFAULT_CAPABILITIES

    firefox_options = config_driver._get_firefox_options()

    assert firefox_options.arguments == expected_arguments
    assert firefox_options.capabilities == expected_capabilities
    assert firefox_options.profile == expected_profile


def test_get_firefox_capabilities_update(config, utils):
    config.add_section('Capabilities')
    config.set('Capabilities', 'pageLoadStrategy', 'eager')
    config_driver = ConfigDriver(config, utils)
    expected_profile = webdriver.FirefoxProfile()
    config_driver._create_firefox_profile = mock.MagicMock(return_value=expected_profile)
    expected_arguments = []
    expected_capabilities = DEFAULT_CAPABILITIES
    expected_capabilities['pageLoadStrategy'] = 'eager'

    firefox_options = config_driver._get_firefox_options()

    assert firefox_options.arguments == expected_arguments
    assert firefox_options.capabilities == expected_capabilities
    assert firefox_options.profile == expected_profile


def test_get_firefox_capabilities_new(config, utils):
    config.add_section('Capabilities')
    config.set('Capabilities', 'browserVersion', '50')
    config_driver = ConfigDriver(config, utils)
    expected_profile = webdriver.FirefoxProfile()
    config_driver._create_firefox_profile = mock.MagicMock(return_value=expected_profile)
    expected_arguments = []
    expected_capabilities = DEFAULT_CAPABILITIES
    expected_capabilities['browserVersion'] = '50'

    firefox_options = config_driver._get_firefox_options()

    assert firefox_options.arguments == expected_arguments
    assert firefox_options.capabilities == expected_capabilities
    assert firefox_options.profile == expected_profile


def test_add_firefox_arguments(config, utils):
    config.add_section('FirefoxArguments')
    config.set('FirefoxArguments', '-private', '')
    config_driver = ConfigDriver(config, utils)
    firefox_options = Options()

    config_driver._add_firefox_arguments(firefox_options)
    assert firefox_options.arguments == ['-private']


def test_add_firefox_arguments_no_section(config, utils):
    config_driver = ConfigDriver(config, utils)
    firefox_options = Options()

    config_driver._add_firefox_arguments(firefox_options)
    assert firefox_options.arguments == []


@mock.patch('toolium.config_driver.webdriver')
def test_create_firefox_profile(webdriver_mock, config, utils):
    config.add_section('Firefox')
    config.set('Firefox', 'profile', '/tmp')
    config.add_section('FirefoxPreferences')
    config.set('FirefoxPreferences', 'browser.download.folderList', '2')
    config.add_section('FirefoxExtensions')
    config.set('FirefoxExtensions', 'firebug', 'resources/firebug-3.0.0-beta.3.xpi')
    config_driver = ConfigDriver(config, utils)

    config_driver._create_firefox_profile()
    webdriver_mock.FirefoxProfile.assert_called_once_with(profile_directory='/tmp')
    webdriver_mock.FirefoxProfile().set_preference.assert_called_once_with('browser.download.folderList', 2)
    webdriver_mock.FirefoxProfile().update_preferences.assert_called_once_with()
    webdriver_mock.FirefoxProfile().add_extension.assert_called_once_with('resources/firebug-3.0.0-beta.3.xpi')
