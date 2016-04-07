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
import unittest

from nose.tools import assert_equal, assert_not_equal

from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool


class DriverWrappersPoolTests(unittest.TestCase):
    def setUp(self):
        # Reset wrappers pool values
        DriverWrappersPool._empty_pool()

        # Create default wrapper
        self.driver_wrapper = DriverWrappersPool.get_default_wrapper()

        # Configure properties
        config_files = ConfigFiles()
        root_path = os.path.dirname(os.path.realpath(__file__))
        config_files.set_config_directory(os.path.join(root_path, 'conf'))
        config_files.set_output_directory(os.path.join(root_path, 'output'))
        self.driver_wrapper.configure(tc_config_files=config_files)

    def test_singleton(self):
        # Request default wrapper
        new_wrapper = DriverWrappersPool.get_default_wrapper()

        # Modify new wrapper
        new_driver_type = 'opera'
        new_wrapper.config.set('Driver', 'type', new_driver_type)

        # Check that both wrappers are the same object
        assert_equal(new_driver_type, self.driver_wrapper.config.get('Driver', 'type'))
        assert_equal(new_driver_type, new_wrapper.config.get('Driver', 'type'))
        assert_equal(self.driver_wrapper, new_wrapper)
        assert_equal(DriverWrappersPool.driver_wrappers[0], self.driver_wrapper)

    def test_multiple(self):
        # Request a new additional wrapper
        new_wrapper = DriverWrapper()

        # Check that wrapper and new_wrapper are different
        assert_not_equal(self.driver_wrapper, new_wrapper)
        assert_equal(DriverWrappersPool.driver_wrappers[0], self.driver_wrapper)
        assert_equal(DriverWrappersPool.driver_wrappers[1], new_wrapper)
