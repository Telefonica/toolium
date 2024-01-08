# -*- coding: utf-8 -*-
"""
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

import mock
import pytest

from toolium.config_parser import ExtendedConfigParser

environment_properties = []


@pytest.fixture
def config():
    root_path = os.path.dirname(os.path.realpath(__file__))
    conf_properties_file = os.path.join(root_path, 'conf', 'properties.cfg')
    config = ExtendedConfigParser()
    config.read(conf_properties_file)

    yield config

    # Remove used environment properties after test
    global environment_properties
    for env_property in environment_properties:
        try:
            del os.environ[env_property]
        except KeyError:
            pass
    environment_properties = []


@pytest.fixture
def logger():
    # Configure logger mock
    logger = mock.MagicMock()
    logger_patch = mock.patch('toolium.config_parser.logger', logger)
    logger_patch.start()

    yield logger

    logger_patch.stop()


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


def test_get(config):
    section = 'AppiumCapabilities'
    option = 'automationName'
    value = 'UiAutomator2'
    assert value == config.get(section, option)


def test_get_with_colon_in_option(config):
    section = 'Capabilities'
    option = 'selenoid:options'
    value = "{'enableVNC': True, 'enableVideo': True}"
    assert value == config.get(section, option)


def test_set_with_colon_in_option(config):
    section = 'Capabilities'
    option = 'selenoid:options'
    orig_value = "{'enableVNC': True, 'enableVideo': True}"
    new_value = "{'enableVNC': False}"

    # Check previous value
    assert orig_value == config.get(section, option)

    # Modify property value and check new value
    config.set(section, option, new_value)
    assert new_value == config.get(section, option)


def test_options_with_colon_in_option(config):
    section = 'Capabilities'
    options = ['selenoid:options', 'cloud:options', 'platformName']
    assert options == config.options(section)


def test_has_option_with_colon_in_option(config):
    section = 'Capabilities'
    option = 'selenoid:options'
    wrong_option = 'selenoid:optionsWrong'
    assert config.has_option(section, option) is True
    assert config.has_option(section, wrong_option) is False


def test_remove_option_with_colon_in_option(config):
    section = 'Capabilities'
    option = 'selenoid:options'
    wrong_option = 'selenoid:optionsWrong'
    assert config.remove_option(section, option) is True
    assert config.remove_option(section, wrong_option) is False
    assert config.get_optional(section, option, default=None) is None


def test_items_with_colon_in_option(config):
    section = 'Capabilities'
    items = [('selenoid:options', "{'enableVNC': True, 'enableVideo': True}"), ('cloud:options', "{'name': 'test'}"),
             ('platformName', 'Android')]
    assert items == config.items(section)


def test_deepcopy(config):
    section = 'AppiumCapabilities'
    option = 'automationName'
    orig_value = 'UiAutomator2'
    new_value = 'espresso'

    # Check previous value
    assert orig_value == config.get(section, option)

    # Copy config object
    new_config = config.deepcopy()

    # Check that both configs have the same property value
    assert orig_value == config.get(section, option)
    assert orig_value == new_config.get(section, option)

    # Modify property value
    new_config.set(section, option, new_value)

    # Check that the value has no changed in original config
    assert orig_value == config.get(section, option)
    assert new_value == new_config.get(section, option)


def test_deepcopy_and_modify_option_with_colon(config):
    section = 'Capabilities'
    configured_option = 'selenoid___options'
    option = 'selenoid:options'
    orig_value = "{'enableVNC': True, 'enableVideo': True}"
    new_value = "{'enableVNC': False}"

    # Check previous value
    assert orig_value == config.get(section, option)

    # Copy config object
    new_config = config.deepcopy()

    # Check that both configs have the same property value
    assert orig_value == config.get(section, option)
    assert orig_value == new_config.get(section, option)

    # Modify property value
    new_config.set(section, configured_option, new_value)

    # Check that the value has no changed in original config
    assert orig_value == config.get(section, option)
    assert new_value == new_config.get(section, option)


toolium_system_properties = (
    # Update value
    ('TOOLIUM_CAPABILITIES_PLATFORMNAME', 'Capabilities', 'platformName', 'Android', 'iOS'),
    # Underscore in value
    ('TOOLIUM_CAPABILITIES_PLATFORMNAME', 'Capabilities', 'platformName', 'Android', 'a_b'),
    # Equal symbol in value
    ('TOOLIUM_CAPABILITIES_PLATFORMNAME', 'Capabilities', 'platformName', 'Android', 'a=b'),
    # Empty value
    ('TOOLIUM_CAPABILITIES_PLATFORMNAME', 'Capabilities', 'platformName', 'Android', ''),
    # Underscore in option
    ('TOOLIUM_SERVER_VIDEO_ENABLED', 'Server', 'video_enabled', 'false', 'true'),
    # New section
    ('TOOLIUM_CUSTOMCAPABILITIES_CUSTOMCAPABILITY', 'CustomCapabilities', 'customCapability', None, 'prueba'),
    # New option
    ('TOOLIUM_CAPABILITIES_CUSTOMCAPABILITY', 'Capabilities', 'customCapability', None, 'prueba'),
    # Lowercase section in name
    ('TOOLIUM_Capabilities_PLATFORMNAME', 'Capabilities', 'platformName', 'Android', 'iOS'),
    # Lowercase option in name
    ('TOOLIUM_CAPABILITIES_PLATFORMName', 'Capabilities', 'platformName', 'Android', 'iOS'),
)


@pytest.mark.parametrize("property_name, section, option, value, new_value", toolium_system_properties)
def test_update_toolium_system_properties(config, property_name, section, option, value, new_value):
    # Check previous value
    if value is None:
        assert not config.has_option(section, option)
    else:
        assert value == config.get(section, option)

    # Change system property and update config
    environment_properties.append(property_name)
    os.environ[property_name] = '{}_{}={}'.format(section, option, new_value)
    config.update_toolium_system_properties(os.environ)

    # Check the new config value
    assert new_value == config.get(section, option)


toolium_system_properties_wrong_format = (
    # No section and option in name
    ('TOOLIUM', 'Capabilities', 'platformName', 'Android', 'Capabilities_platformName=iOS'),
    # No option in name
    ('TOOLIUM_CAPABILITIES', 'Capabilities', 'platformName', 'Android', 'Capabilities_platformName=iOS'),
    # Option in name different from option in value
    ('TOOLIUM_CAPABILITIES_PLATFORM', 'Capabilities', 'platformName', 'Android', 'Capabilities_platformName=iOS'),
    # Additional param in name
    ('TOOLIUM_CAPABILITIES_PLATFORMNAME_WRONG', 'Capabilities', 'platformName', 'Android',
     'Capabilities_platformName=iOS'),
    # No option in value
    ('TOOLIUM_CAPABILITIES_PLATFORMNAME', 'Capabilities', 'platformName', 'Android', 'Capabilities=iOS'),
    # Additional param in value
    ('TOOLIUM_CAPABILITIES_PLATFORMNAME', 'Capabilities', 'platformName', 'Android',
     'Capabilities_platformName_wrong=iOS'),
    # No equal in value
    ('TOOLIUM_CAPABILITIES_PLATFORMNAME', 'Capabilities', 'platformName', 'Android', 'Capabilities_platformName iOS'),
    # Empty section
    ('TOOLIUM__PLATFORMNAME', 'Capabilities', 'platformName', 'Android', '_platformName=iOS'),
    # Empty option
    ('TOOLIUM_CAPABILITIES_', 'Capabilities', 'platformName', 'Android', 'Capabilities_=iOS'),
    # No toolium system property
    ('WRONGNAME', 'Capabilities', 'platformName', 'Android', 'platformName_Android=iOS'),
)


@pytest.mark.parametrize("property_name, section, option, value, property_value",
                         toolium_system_properties_wrong_format)
def test_update_toolium_system_properties_wrong_format(config, logger, property_name, section, option, value,
                                                       property_value):
    # Check previous value
    if value is None:
        assert not config.has_option(section, option)
    else:
        assert value == config.get(section, option)

    # Change system property and update config
    environment_properties.append(property_name)
    os.environ[property_name] = property_value
    config.update_toolium_system_properties(os.environ)

    # Check that config value has not changed
    assert value == config.get(section, option)

    # Check logging error message
    if property_name.startswith('TOOLIUM'):
        logger.warning.assert_called_once_with('A toolium system property is configured but its name does not math with'
                                               ' section and option in value (use TOOLIUM_[SECTION]_[OPTION]=[Section]_'
                                               '[option]=value): %s=%s', property_name, property_value)
    else:
        logger.warning.assert_not_called()


toolium_system_properties_special = (
    ('TOOLIUM_CONFIG_ENVIRONMENT', 'value1'),
    ('TOOLIUM_OUTPUT_DIRECTORY', 'value2'),
    ('TOOLIUM_OUTPUT_LOG_FILENAME', 'value3'),
    ('TOOLIUM_CONFIG_DIRECTORY', 'value4'),
    ('TOOLIUM_CONFIG_LOG_FILENAME', 'value5'),
    ('TOOLIUM_CONFIG_PROPERTIES_FILENAMES', 'value6'),
    ('TOOLIUM_VISUAL_BASELINE_DIRECTORY', 'value7'),
)


@pytest.mark.parametrize("property_name, property_value", toolium_system_properties_special)
def test_update_toolium_system_properties_special(config, logger, property_name, property_value):
    # Change system property and update config
    environment_properties.append(property_name)
    os.environ[property_name] = property_value
    previous_config = config.deepcopy()
    config.update_toolium_system_properties(os.environ)

    # Check that config has not been updated and error message is not logged
    assert previous_config == config, 'Config has been updated'
    logger.warning.assert_not_called()


def test_update_properties_behave(config):
    section = 'Capabilities'
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
