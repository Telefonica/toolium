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

from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.config_files import ConfigFiles


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
        new_browser = 'opera'
        new_wrapper.config.set('Browser', 'browser', new_browser)

        # Check that both wrappers are the same object
        self.assertEqual(new_browser, self.driver_wrapper.config.get('Browser', 'browser'))
        self.assertEqual(new_browser, new_wrapper.config.get('Browser', 'browser'))
        self.assertEqual(self.driver_wrapper, new_wrapper)
        self.assertEqual(DriverWrappersPool.driver_wrappers[0], self.driver_wrapper)

    def test_multiple(self):
        # Request a new additional wrapper
        new_wrapper = DriverWrapper()

        # Check that wrapper and new_wrapper are different
        self.assertNotEqual(self.driver_wrapper, new_wrapper)
        self.assertEqual(DriverWrappersPool.driver_wrappers[0], self.driver_wrapper)
        self.assertEqual(DriverWrappersPool.driver_wrappers[1], new_wrapper)
