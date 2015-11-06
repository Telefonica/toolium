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
import logging

import mock

from toolium.test_cases import BasicTestCase


class MockTestClass(BasicTestCase):
    def setUp(self):
        root_path = os.path.dirname(os.path.realpath(__file__))
        self.set_config_directory(os.path.join(root_path, 'conf'))
        super(MockTestClass, self).setUp()

    def mock_pass(self):
        pass

    def mock_fail(self):
        raise AssertionError('test error')


def run_mock(test_name):
    """Run a unit test from mock class

    :param test_name: test name that must be executed
    :returns: test instance
    """
    suite = unittest.TestSuite()
    test = MockTestClass(test_name)
    suite.addTest(test)
    unittest.TextTestRunner().run(suite)
    return test


class BasicTestCaseTests(unittest.TestCase):
    def test_tearDown_pass(self):
        # Configure logger mock
        logger = mock.MagicMock()
        logging.getLogger = mock.MagicMock(return_value=logger)

        test = run_mock('mock_pass')
        self.assertTrue(test._test_passed)

        # Check logging message
        expected_response = "The test 'MockTestClass.mock_pass' has passed"
        logger.info.assert_called_with(expected_response)

    def test_tearDown_fail(self):
        # Configure logger mock
        logger = mock.MagicMock()
        logging.getLogger = mock.MagicMock(return_value=logger)

        test = run_mock('mock_fail')
        self.assertFalse(test._test_passed)

        # Check logging error message
        expected_response = "The test 'MockTestClass.mock_fail' has failed: test error"
        logger.error.assert_called_with(expected_response)
