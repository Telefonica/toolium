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

import mock
import pytest


def run_mock(test_name):
    """Run a unit test from mock class

    :param test_name: test name that must be executed
    :returns: test instance
    """
    # BasicTestCase import should be inside method to avoid collecting tests error in behave with python 3.7
    from toolium.test_cases import BasicTestCase

    class MockTestClass(BasicTestCase):
        def setUp(self):
            root_path = os.path.dirname(os.path.realpath(__file__))
            self.config_files.set_config_directory(os.path.join(root_path, 'conf'))
            super(MockTestClass, self).setUp()

        def mock_pass(self):
            pass

        def mock_fail(self):
            raise AssertionError('test error')

    suite = unittest.TestSuite()
    test = MockTestClass(test_name)
    suite.addTest(test)
    unittest.TextTestRunner().run(suite)
    return test


@pytest.yield_fixture
def logger():
    # Configure logger mock
    logger = mock.MagicMock()
    logger_patch = mock.patch('logging.getLogger', mock.MagicMock(return_value=logger))
    logger_patch.start()

    yield logger

    logger_patch.stop()


def test_tear_down_pass(logger):
    test = run_mock('mock_pass')
    assert test._test_passed is True

    # Check logging messages
    logger.info.assert_has_calls([mock.call('Running new test: %s', 'MockTestClass.mock_pass'),
                                  mock.call("The test '%s' has passed", 'MockTestClass.mock_pass')])


def test_tear_down_fail(logger):
    test = run_mock('mock_fail')
    assert test._test_passed is False

    # Check logging error messages
    logger.info.assert_called_once_with('Running new test: %s', 'MockTestClass.mock_fail')
    logger.error.assert_called_once_with("The test '%s' has failed: %s", 'MockTestClass.mock_fail', 'test error')
