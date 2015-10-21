# -*- coding: utf-8 -*-
u"""
Copyright 2015 Telefónica Investigación y Desarrollo, S.A.U.
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
import os

from ddt import ddt, data, unpack

from toolium.config_parser import ExtendedConfigParser

optional_values = (
    ('No section', 'No option', None, None),
    ('No section', 'No option', 'chrome', 'chrome'),
    ('Browser', 'No option', None, None),
    ('Browser', 'No option', 'chrome', 'chrome'),
    ('Browser', 'browser', None, 'firefox'),
    ('Browser', 'browser', 'chrome', 'firefox'),
)

optional_boolean_values = (
    ('No section', 'No option', None, False),
    ('No section', 'No option', True, True),
    ('Server', 'No option', None, False),
    ('Server', 'No option', False, False),
    ('Server', 'enabled', None, True),
    ('Server', 'enabled', False, True),
)


@ddt
class ExtendedConfigParserTests(unittest.TestCase):
    def setUp(self):
        root_path = os.path.dirname(os.path.realpath(__file__))
        conf_properties_file = os.path.join(root_path, 'conf', 'properties.cfg')
        self.config = ExtendedConfigParser()
        self.config.read(conf_properties_file)

    @data(*optional_values)
    @unpack
    def test_get_optional(self, section, option, default, response):
        if default:
            self.assertEquals(response, self.config.get_optional(section, option, default))
        else:
            self.assertEquals(response, self.config.get_optional(section, option))

    @data(*optional_boolean_values)
    @unpack
    def test_getboolean_optional(self, section, option, default, response):
        if default:
            self.assertEquals(response, self.config.getboolean_optional(section, option, default))
        else:
            self.assertEquals(response, self.config.getboolean_optional(section, option))

    def test_deepcopy(self):
        section = 'AppiumCapabilities'
        option = 'automationName'
        orig_value = 'Appium'
        new_value = 'Selendroid'

        # Check previous value
        self.assertEquals(orig_value, self.config.get(section, option))

        # Copy config object and modify a property
        new_config = self.config.deepcopy()
        new_config.set(section, option, new_value)

        # Check that the value has no changed in original config
        self.assertEquals(orig_value, self.config.get(section, option))
        self.assertEquals(new_value, new_config.get(section, option))

    def test_update_from_system_properties(self):
        section = 'AppiumCapabilities'
        option = 'platformName'
        orig_value = 'Android'
        new_value = 'iOS'

        # Check previous value
        self.assertEquals(orig_value, self.config.get(section, option))

        # Change system property and update config
        os.environ[section + '_' + option] = new_value
        self.config.update_from_system_properties()

        # Check the new config value
        self.assertEquals(new_value, self.config.get(section, option))
