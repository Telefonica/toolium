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

import pytest

from toolium.config_files import ConfigFiles


@pytest.fixture
def config_files():
    return ConfigFiles()


def test_empty_config_files(config_files):
    assert config_files.config_directory is None
    assert config_files.output_directory is None
    assert config_files.visual_baseline_directory is None
    assert config_files.config_properties_filenames is None
    assert config_files.config_log_filename is None
    assert config_files.output_log_filename is None


def test_set_config_directory(config_files):
    directory = '/tmp/fake'
    config_files.set_config_directory(directory)
    assert directory == config_files.config_directory


def test_set_output_directory(config_files):
    directory = '/tmp/fake'
    config_files.set_output_directory(directory)
    assert directory == config_files.output_directory


def test_set_visual_baseline_directory(config_files):
    directory = '/tmp/fake'
    config_files.set_visual_baseline_directory(directory)
    assert directory == config_files.visual_baseline_directory


def test_set_config_properties_filenames(config_files):
    config_files.set_config_properties_filenames('properties.cfg', 'local-properties.cfg')
    assert 'properties.cfg;local-properties.cfg' == config_files.config_properties_filenames


def test_set_config_log_filename(config_files):
    filename = 'logging.conf'
    config_files.set_config_log_filename(filename)
    assert filename == config_files.config_log_filename


def test_set_output_log_filename(config_files):
    filename = 'output.log'
    config_files.set_output_log_filename(filename)
    assert filename == config_files.output_log_filename
