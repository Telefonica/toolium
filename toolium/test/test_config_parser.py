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

import os

import pytest

from toolium.config_parser import ExtendedConfigParser

optional_values = (
    ('No section', 'No option', None, None),
    ('No section', 'No option', 'chrome', 'chrome'),
    ('Driver', 'No option', None, None),
    ('Driver', 'No option', 'chrome', 'chrome'),
    ('Driver', 'type', None, 'firefox'),
    ('Driver', 'type', 'chrome', 'firefox'),
)

optional_boolean_values = (
    ('No section', 'No option', None, False),
    ('No section', 'No option', True, True),
    ('Server', 'No option', None, False),
    ('Server', 'No option', False, False),
    ('Server', 'enabled', None, True),
    ('Server', 'enabled', False, True),
)


@pytest.fixture
def config():
    root_path = os.path.dirname(os.path.realpath(__file__))
    conf_properties_file = os.path.join(root_path, 'conf', 'properties.cfg')
    config = ExtendedConfigParser()
    config.read(conf_properties_file)
    return config


@pytest.mark.parametrize("section, option, default, response", optional_values)
def test_get_optional(section, option, default, response, config):
    if default:
        assert response == config.get_optional(section, option, default)
    else:
        assert response == config.get_optional(section, option)


@pytest.mark.parametrize("section, option, default, response", optional_boolean_values)
def test_getboolean_optional(section, option, default, response, config):
    if default:
        assert response == config.getboolean_optional(section, option, default)
    else:
        assert response == config.getboolean_optional(section, option)


def test_deepcopy(config):
    section = 'AppiumCapabilities'
    option = 'automationName'
    orig_value = 'Appium'
    new_value = 'Selendroid'

    # Check previous value
    assert orig_value == config.get(section, option)

    # Copy config object and modify a property
    new_config = config.deepcopy()
    new_config.set(section, option, new_value)

    # Check that the value has no changed in original config
    assert orig_value == config.get(section, option)
    assert new_value == new_config.get(section, option)


def test_update_properties_environ(config):
    section = 'AppiumCapabilities'
    option = 'platformName'
    orig_value = 'Android'
    new_value = 'iOS'

    # Check previous value
    assert orig_value == config.get(section, option)

    # Change system property and update config
    os.environ['{}_{}'.format(section, option)] = new_value
    config.update_properties(os.environ)

    # Check the new config value
    assert new_value == config.get(section, option)


def test_update_properties_behave(config):
    section = 'AppiumCapabilities'
    option = 'platformName'
    orig_value = 'Android'
    new_value = 'iOS'

    # Check previous value
    assert orig_value == config.get(section, option)

    # Change system property and update config
    behave_properties = {'{}_{}'.format(section, option): new_value}
    config.update_properties(behave_properties)

    # Check the new config value
    assert new_value == config.get(section, option)


strings_to_translate = (
    ('{Driver_type}', 'firefox'),
    ('', ''),
    ('[{Driver_type}] ', '[firefox] '),
    ('{Driver_type}/{Server_enabled}', 'firefox/true'),
    ('{AppiumCapabilities_deviceName} {Server}', 'Android Emulator {Server}'),
)


@pytest.mark.parametrize("string_with_variables, translated_string", strings_to_translate)
def test_translate_config_variables(config, string_with_variables, translated_string):
    assert translated_string == config.translate_config_variables(string_with_variables)
