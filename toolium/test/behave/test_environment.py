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
import unittest

import mock
from ddt import ddt, data, unpack
from nose.tools import assert_equal, assert_is_none

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


@ddt
class EnvironmentJiraTests(unittest.TestCase):
    @data(*tags)
    @unpack
    def test_get_jira_key_from_scenario(self, tag_list, jira_key):
        scenario = mock.Mock()
        scenario.tags = tag_list

        # Extract Jira key and compare with expected key
        assert_equal(jira_key, get_jira_key_from_scenario(scenario))


class EnvironmentTests(unittest.TestCase):
    @mock.patch('toolium.behave.environment.create_and_configure_wrapper')
    def test_before_all(self, create_and_configure_wrapper):
        # Create context mock
        context = mock.MagicMock()
        context.config.userdata.get.return_value = None
        context.config_files = ConfigFiles()

        before_all(context)

        # Check that configuration folder is the same as environment folder
        expected_config_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'conf')
        assert_equal(context.config_files.config_directory, expected_config_directory)
        assert_is_none(context.config_files.config_properties_filenames)
        assert_is_none(context.config_files.config_log_filename)

    @mock.patch('toolium.behave.environment.create_and_configure_wrapper')
    def test_before_all_env(self, create_and_configure_wrapper):
        # Create context mock
        context = mock.MagicMock()
        context.config.userdata.get.return_value = 'os'
        context.config_files = ConfigFiles()

        before_all(context)

        # Check that configuration folder is the same as environment folder and configuration files are 'os' files
        expected_config_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'conf')
        expected_config_properties_filenames = 'properties.cfg;os-properties.cfg;local-os-properties.cfg'
        assert_equal(context.config_files.config_directory, expected_config_directory)
        assert_equal(context.config_files.config_properties_filenames, expected_config_properties_filenames)
        assert_is_none(context.config_files.config_log_filename)
