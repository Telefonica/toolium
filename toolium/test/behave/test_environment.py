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

import unittest

import mock
from ddt import ddt, data, unpack
from nose.tools import assert_equal

from toolium.behave.environment import get_jira_key_from_scenario

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
class EnvironmentTests(unittest.TestCase):
    @data(*tags)
    @unpack
    def test_get_jira_key_from_scenario(self, tag_list, jira_key):
        scenario = mock.Mock()
        scenario.tags = tag_list

        # Extract Jira key and compare with expected key
        assert_equal(jira_key, get_jira_key_from_scenario(scenario))
