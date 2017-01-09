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

from toolium.behave.environment import get_jira_key_from_scenario, before_all
from toolium.config_files import ConfigFiles

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
    ('env'),
    ('Config_environment'),
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
    assert context.config_files.config_properties_filenames is None
    assert context.config_files.config_log_filename is None
    assert os.environ['Config_environment'] == 'os'
    del os.environ["Config_environment"]
