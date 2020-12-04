# -*- coding: utf-8 -*-
u"""
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

import mock
import pytest

from toolium.behave.environment import (get_jira_key_from_scenario, before_all, before_feature, before_scenario,
                                        after_scenario, after_feature, after_all)
from toolium.config_files import ConfigFiles
from toolium.config_parser import ExtendedConfigParser

tags = (
    (["jira('PROJECT-32')"], 'PROJECT-32'),
    (["jira=PROJECT-32"], 'PROJECT-32'),
    (["jira(PROJECT-32)"], 'PROJECT-32'),
    (["jira='PROJECT-32'"], 'PROJECT-32'),
    (["jiraPROJECT-32"], 'PROJECT-32'),
    (["jira"], None),
    (["PROJECT-32"], None),
    (['slow', "jira('PROJECT-32')", 'critical'], 'PROJECT-32'),
    (['slow', "PROJECT-32", 'critical'], None),
    (['slow', "jira('PROJECT-32')", "jira('PROJECT-33')"], 'PROJECT-32'),
)


@pytest.mark.parametrize("tag_list, jira_key", tags)
def test_get_jira_key_from_scenario(tag_list, jira_key):
    scenario = mock.Mock()
    scenario.tags = tag_list

    # Extract Jira key and compare with expected key
    assert jira_key == get_jira_key_from_scenario(scenario)


@mock.patch('toolium.behave.environment.create_and_configure_wrapper')
def test_before_all(create_and_configure_wrapper):
    # Create context mock
    context = mock.MagicMock()
    context.config.userdata.get.return_value = None
    context.config_files = ConfigFiles()

    before_all(context)

    # Check that configuration folder is the same as environment folder
    expected_config_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'conf')
    assert context.config_files.config_directory == expected_config_directory
    assert context.config_files.config_properties_filenames is None
    assert context.config_files.config_log_filename is None


properties = (
    'env',
    'Config_environment',
)


@pytest.mark.parametrize("property_name", properties)
@mock.patch('toolium.behave.environment.create_and_configure_wrapper')
def test_before_all_config_environment(create_and_configure_wrapper, property_name):
    # Create context mock
    context = mock.MagicMock()
    context.config.userdata.get.side_effect = lambda x: 'os' if x == property_name else None
    context.config_files = ConfigFiles()

    before_all(context)

    # Check that configuration folder is the same as environment folder and property 'Config_environment' is configured
    expected_config_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'conf')
    assert context.config_files.config_directory == expected_config_directory
    assert context.config_files.config_properties_filenames == 'properties.cfg;os-properties.cfg;local-os-properties.cfg'
    assert context.config_files.config_log_filename is None
    assert os.environ['Config_environment'] == 'os'
    del os.environ["Config_environment"]


@mock.patch('toolium.behave.environment.start_driver')
def test_before_feature(start_driver):
    # Create context mock
    context = mock.MagicMock()
    context.toolium_config = ExtendedConfigParser()
    feature = mock.MagicMock()
    feature.tags = ['a', 'b']

    before_feature(context, feature)

    # Check that start_driver is not called
    start_driver.assert_not_called()


@mock.patch('toolium.behave.environment.start_driver')
def test_before_feature_reuse_driver(start_driver):
    # Create context mock
    context = mock.MagicMock()
    context.toolium_config = ExtendedConfigParser()
    feature = mock.MagicMock()
    feature.tags = ['a', 'reuse_driver', 'b']

    before_feature(context, feature)

    # Check that start_driver is called when reuse_driver tag
    start_driver.assert_called_once_with(context, False)
    assert context.reuse_driver_from_tags is True


@mock.patch('toolium.behave.environment.start_driver')
def test_before_feature_reuse_driver_no_driver(start_driver):
    # Create context mock
    context = mock.MagicMock()
    context.toolium_config = ExtendedConfigParser()
    feature = mock.MagicMock()
    feature.tags = ['a', 'reuse_driver', 'b', 'no_driver']

    before_feature(context, feature)

    # Check that start_driver is called when reuse_driver tag, with True no_driver param
    start_driver.assert_called_once_with(context, True)
    assert context.reuse_driver_from_tags is True


@mock.patch('toolium.behave.environment.add_assert_screenshot_methods')
@mock.patch('toolium.behave.environment.DriverWrappersPool')
@mock.patch('toolium.behave.environment.start_driver')
def test_before_scenario(start_driver, DriverWrappersPool, add_assert_screenshot_methods):
    # Create context mock
    context = mock.MagicMock()
    context.toolium_config = ExtendedConfigParser()
    scenario = mock.MagicMock()
    scenario.tags = ['a', 'b']

    before_scenario(context, scenario)

    # Check that start_driver is called
    start_driver.assert_called_once_with(context, False)
    DriverWrappersPool.stop_drivers.assert_not_called()


@mock.patch('toolium.behave.environment.add_assert_screenshot_methods')
@mock.patch('toolium.behave.environment.DriverWrappersPool')
@mock.patch('toolium.behave.environment.start_driver')
def test_before_scenario_reset_driver(start_driver, DriverWrappersPool, add_assert_screenshot_methods):
    # Create context mock
    context = mock.MagicMock()
    context.toolium_config = ExtendedConfigParser()
    scenario = mock.MagicMock()
    scenario.tags = ['a', 'reset_driver', 'b']

    before_scenario(context, scenario)

    # Check that start_driver and stop drivers are called
    start_driver.assert_called_once_with(context, False)
    DriverWrappersPool.stop_drivers.assert_called_once_with()


@mock.patch('toolium.behave.environment.add_assert_screenshot_methods')
@mock.patch('toolium.behave.environment.start_driver')
def test_before_scenario_no_driver(start_driver, add_assert_screenshot_methods):
    # Create context mock
    context = mock.MagicMock()
    context.toolium_config = ExtendedConfigParser()
    scenario = mock.MagicMock()
    scenario.tags = ['a', 'no_driver', 'b']

    before_scenario(context, scenario)

    # Check that start_driver is called
    start_driver.assert_called_once_with(context, True)


@mock.patch('toolium.behave.environment.add_assert_screenshot_methods')
@mock.patch('toolium.behave.environment.start_driver')
def test_before_scenario_no_driver_feature(start_driver, add_assert_screenshot_methods):
    # Create context mock
    context = mock.MagicMock()
    context.toolium_config = ExtendedConfigParser()
    scenario = mock.MagicMock()
    scenario.tags = ['a', 'b']
    scenario.feature.tags = ['no_driver']

    before_scenario(context, scenario)

    # Check that start_driver is called
    start_driver.assert_called_once_with(context, True)


@mock.patch('toolium.behave.environment.DriverWrappersPool')
def test_after_scenario_passed(DriverWrappersPool):
    # Create context mock
    context = mock.MagicMock()
    context.global_status = {'test_passed': True}
    scenario = mock.MagicMock()
    scenario.name = 'name'
    scenario.status = 'passed'

    after_scenario(context, scenario)

    # Check that close_drivers is called
    assert context.global_status['test_passed'] is True
    DriverWrappersPool.close_drivers.assert_called_once_with(context=context, scope='function', test_name='name',
                                                             test_passed=True)


@mock.patch('toolium.behave.environment.DriverWrappersPool')
def test_after_scenario_failed(DriverWrappersPool):
    # Create context mock
    context = mock.MagicMock()
    context.global_status = {'test_passed': True}
    scenario = mock.MagicMock()
    scenario.name = 'name'
    scenario.status = 'failed'

    after_scenario(context, scenario)

    # Check that close_drivers is called
    assert context.global_status['test_passed'] is False
    DriverWrappersPool.close_drivers.assert_called_once_with(context=context, scope='function', test_name='name',
                                                             test_passed=False)


@mock.patch('toolium.behave.environment.DriverWrappersPool')
def test_after_scenario_skipped(DriverWrappersPool):
    # Create context mock
    context = mock.MagicMock()
    context.global_status = {'test_passed': True}
    scenario = mock.MagicMock()
    scenario.name = 'name'
    scenario.status = 'skipped'

    after_scenario(context, scenario)

    # Check that close_drivers is not called
    assert context.global_status['test_passed'] is True
    DriverWrappersPool.close_drivers.assert_not_called()


@mock.patch('toolium.behave.environment.DriverWrappersPool')
def test_after_feature(DriverWrappersPool):
    # Create context mock
    context = mock.MagicMock()
    context.global_status = {'test_passed': True}
    feature = mock.MagicMock()
    feature.name = 'name'

    after_feature(context, feature)

    # Check that close_drivers is called
    DriverWrappersPool.close_drivers.assert_called_once_with(scope='module', test_name='name', test_passed=True)


@mock.patch('toolium.behave.environment.DriverWrappersPool')
def test_after_all(DriverWrappersPool):
    # Create context mock
    context = mock.MagicMock()
    context.global_status = {'test_passed': True}

    after_all(context)

    # Check that close_drivers is called
    DriverWrappersPool.close_drivers.assert_called_once_with(scope='session', test_name='multiple_tests',
                                                             test_passed=True)
