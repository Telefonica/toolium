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
from selenium.webdriver.edge.options import Options

from toolium.config_driver import ConfigDriver
from toolium.config_parser import ExtendedConfigParser
from toolium.driver_wrappers_pool import DriverWrappersPool


DEFAULT_CAPABILITIES = {'browserName': 'MicrosoftEdge', 'pageLoadStrategy': 'normal'}


@pytest.fixture
def config():
    config_parser = ExtendedConfigParser()
    config_parser.add_section('Server')
    config_parser.add_section('Driver')
    return config_parser


@pytest.fixture
def utils():
    utils = mock.MagicMock()
    utils.get_driver_name.return_value = 'edge'
    return utils


@mock.patch('toolium.config_driver.EdgeOptions')
@mock.patch('toolium.config_driver.EdgeService')
@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_edge_no_driver_path(webdriver_mock, service, options, config, utils):
    config.set('Driver', 'type', 'edge')
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''

    config_driver._create_local_driver()
    service.assert_called_once_with()
    options.assert_called_once_with()
    webdriver_mock.Edge.assert_called_once_with(service=service(), options=options())


@mock.patch('toolium.config_driver.EdgeOptions')
@mock.patch('toolium.config_driver.EdgeService')
@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_edge_driver_path(webdriver_mock, service, options, config, utils):
    config.set('Driver', 'type', 'edge')
    config.set('Driver', 'edge_driver_path', '/tmp/driver')
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''

    config_driver._create_local_driver()
    options.assert_called_once_with()
    service.assert_called_once_with(executable_path='/tmp/driver')
    webdriver_mock.Edge.assert_called_once_with(service=service(), options=options())


def test_get_edge_options(config, utils):
    config_driver = ConfigDriver(config, utils)
    expected_arguments = []
    expected_capabilities = DEFAULT_CAPABILITIES

    options = config_driver._get_edge_options()

    assert options.arguments == expected_arguments
    assert options.capabilities == expected_capabilities


def test_get_edge_options_capabilities_update(config, utils):
    config.add_section('Capabilities')
    config.set('Capabilities', 'pageLoadStrategy', 'eager')
    config_driver = ConfigDriver(config, utils)
    expected_arguments = []
    expected_capabilities = DEFAULT_CAPABILITIES.copy()
    expected_capabilities['pageLoadStrategy'] = 'eager'

    options = config_driver._get_edge_options()

    assert options.arguments == expected_arguments
    assert options.capabilities == expected_capabilities


def test_get_edge_options_capabilities_new(config, utils):
    config.add_section('Capabilities')
    config.set('Capabilities', 'browserVersion', '50')
    # TODO: next line it should not be needed, but config object has not been cleaned after previous test
    config.set('Capabilities', 'pageLoadStrategy', 'normal')
    config_driver = ConfigDriver(config, utils)
    expected_arguments = []
    expected_capabilities = DEFAULT_CAPABILITIES.copy()
    expected_capabilities['browserVersion'] = '50'

    options = config_driver._get_edge_options()

    assert options.arguments == expected_arguments
    assert options.capabilities == expected_capabilities


def test_get_edge_options_with_previous_capabilities(config, utils):
    config_driver = ConfigDriver(config, utils)
    expected_arguments = []
    expected_capabilities = DEFAULT_CAPABILITIES.copy()
    expected_capabilities['browserVersion'] = '100'

    previous_capabilities = {'browserVersion': '100'}
    options = config_driver._get_edge_options(previous_capabilities)

    assert options.arguments == expected_arguments
    assert options.capabilities == expected_capabilities


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_edge(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'edge')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''
    expected_capabilities = DEFAULT_CAPABILITIES

    config_driver._create_remote_driver()

    # Check that edge options contain expected capabilities
    args, kwargs = webdriver_mock.Remote.call_args
    options = kwargs['options']
    assert isinstance(options, Options)
    assert options.capabilities == expected_capabilities
    webdriver_mock.Remote.assert_called_once_with(command_executor=f'{server_url}/wd/hub', options=options)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_edge_with_version_and_platform(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'edge-50-on-linux')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''
    expected_capabilities = DEFAULT_CAPABILITIES.copy()
    expected_capabilities['browserVersion'] = '50'
    expected_capabilities['platformName'] = 'linux'

    config_driver._create_remote_driver()

    # Check that edge options contain expected capabilities
    args, kwargs = webdriver_mock.Remote.call_args
    options = kwargs['options']
    assert isinstance(options, Options)
    assert options.capabilities == expected_capabilities
    webdriver_mock.Remote.assert_called_once_with(command_executor=f'{server_url}/wd/hub', options=options)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_edge_with_version_and_platform_uppercase(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'edge-50-on-LINUX')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    config_driver = ConfigDriver(config, utils)
    DriverWrappersPool.output_directory = ''
    expected_capabilities = DEFAULT_CAPABILITIES.copy()
    expected_capabilities['browserVersion'] = '50'
    expected_capabilities['platformName'] = 'linux'

    config_driver._create_remote_driver()

    # Check that edge options contain expected capabilities
    args, kwargs = webdriver_mock.Remote.call_args
    options = kwargs['options']
    assert isinstance(options, Options)
    assert options.capabilities == expected_capabilities
    webdriver_mock.Remote.assert_called_once_with(command_executor=f'{server_url}/wd/hub', options=options)
