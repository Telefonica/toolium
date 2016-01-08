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

from nose.tools import assert_is_none, assert_equal

from toolium.config_files import ConfigFiles


class ConfigFilesTests(unittest.TestCase):
    def test_empty_config_files(self):
        config_files = ConfigFiles()
        assert_is_none(config_files.config_directory)
        assert_is_none(config_files.output_directory)
        assert_is_none(config_files.config_properties_filenames)
        assert_is_none(config_files.config_log_filename)
        assert_is_none(config_files.output_log_filename)

    def test_set_config_directory(self):
        config_files = ConfigFiles()
        directory = '/tmp/fake'
        config_files.set_config_directory(directory)
        assert_equal(directory, config_files.config_directory)

    def test_set_output_directory(self):
        config_files = ConfigFiles()
        directory = '/tmp/fake'
        config_files.set_output_directory(directory)
        assert_equal(directory, config_files.output_directory)

    def test_set_config_properties_filenames(self):
        config_files = ConfigFiles()
        config_files.set_config_properties_filenames('properties.cfg', 'local-properties.cfg')
        assert_equal('properties.cfg;local-properties.cfg', config_files.config_properties_filenames)

    def test_set_config_log_filename(self):
        config_files = ConfigFiles()
        filename = 'logging.conf'
        config_files.set_config_log_filename(filename)
        assert_equal(filename, config_files.config_log_filename)

    def test_set_output_log_filename(self):
        config_files = ConfigFiles()
        filename = 'output.log'
        config_files.set_output_log_filename(filename)
        assert_equal(filename, config_files.output_log_filename)
