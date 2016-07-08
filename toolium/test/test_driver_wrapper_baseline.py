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

from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool

root_path = os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def driver_wrapper():
    # Reset wrappers pool values
    DriverWrappersPool._empty_pool()
    DriverWrapper.config_properties_filenames = None

    # Create a new wrapper
    new_driver_wrapper = DriverWrappersPool.get_default_wrapper()

    # Configure wrapper
    config_files = ConfigFiles()
    config_files.set_config_directory(os.path.join(root_path, 'conf'))
    config_files.set_output_directory(os.path.join(root_path, 'output'))
    config_files.set_config_log_filename('logging.conf')
    DriverWrappersPool.configure_common_directories(config_files)
    new_driver_wrapper.configure_properties()

    return new_driver_wrapper


def test_configure_visual_baseline_not_configured(driver_wrapper):
    driver_wrapper.config.remove_option('VisualTests', 'baseline_name')

    driver_wrapper.configure_visual_baseline()

    expected_baseline_directory = os.path.join(root_path, 'output', 'visualtests', 'baseline', 'firefox')
    assert driver_wrapper.baseline_name == 'firefox'
    assert driver_wrapper.visual_baseline_directory == expected_baseline_directory


def test_configure_visual_baseline_driver_type(driver_wrapper):
    driver_wrapper.config.set('VisualTests', 'baseline_name', '{Driver_type}')

    driver_wrapper.configure_visual_baseline()

    expected_baseline_directory = os.path.join(root_path, 'output', 'visualtests', 'baseline', 'firefox')
    assert driver_wrapper.baseline_name == 'firefox'
    assert driver_wrapper.visual_baseline_directory == expected_baseline_directory


def test_update_visual_baseline_platform_version(driver_wrapper):
    # Configure baseline and driver mock
    driver_wrapper.config.set('VisualTests', 'baseline_name', 'ios_{PlatformVersion}')
    driver_wrapper.driver = mock.MagicMock()
    driver_wrapper.driver.desired_capabilities.__getitem__.return_value = '9.3'

    driver_wrapper.configure_visual_baseline()
    driver_wrapper.update_visual_baseline()

    expected_baseline_directory = os.path.join(root_path, 'output', 'visualtests', 'baseline', 'ios_9.3')
    assert driver_wrapper.baseline_name == 'ios_9.3'
    assert driver_wrapper.visual_baseline_directory == expected_baseline_directory


def test_update_visual_baseline_version(driver_wrapper):
    # Configure baseline and driver mock
    driver_wrapper.config.set('VisualTests', 'baseline_name', 'chrome_{Version}')
    driver_wrapper.driver = mock.MagicMock()
    driver_wrapper.driver.desired_capabilities.__getitem__.return_value = '51.0.2704.103'

    driver_wrapper.configure_visual_baseline()
    driver_wrapper.update_visual_baseline()

    expected_baseline_directory = os.path.join(root_path, 'output', 'visualtests', 'baseline', 'chrome_51.0')
    assert driver_wrapper.baseline_name == 'chrome_51.0'
    assert driver_wrapper.visual_baseline_directory == expected_baseline_directory


def test_update_visual_baseline_remote_node(driver_wrapper):
    # Configure baseline and remote node
    driver_wrapper.config.set('VisualTests', 'baseline_name', 'firefox_{RemoteNode}')
    driver_wrapper.remote_node = '255.255.255.255'

    driver_wrapper.configure_visual_baseline()
    driver_wrapper.update_visual_baseline()

    expected_baseline_directory = os.path.join(root_path, 'output', 'visualtests', 'baseline',
                                               'firefox_255.255.255.255')
    assert driver_wrapper.baseline_name == 'firefox_255.255.255.255'
    assert driver_wrapper.visual_baseline_directory == expected_baseline_directory


def test_update_visual_baseline_remote_node_empty(driver_wrapper):
    # Configure baseline
    driver_wrapper.config.set('VisualTests', 'baseline_name', 'firefox_{RemoteNode}')

    driver_wrapper.configure_visual_baseline()
    driver_wrapper.update_visual_baseline()

    expected_baseline_directory = os.path.join(root_path, 'output', 'visualtests', 'baseline', 'firefox_None')
    assert driver_wrapper.baseline_name == 'firefox_None'
    assert driver_wrapper.visual_baseline_directory == expected_baseline_directory
