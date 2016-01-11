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

import mock
import requests_mock
from nose.tools import assert_equal, assert_in, assert_raises
from requests.exceptions import ConnectionError

from toolium import jira
from toolium.driver_wrappers_pool import DriverWrappersPool


class JiraTests(unittest.TestCase):
    def tearDown(self):
        # Clear jira module configuration
        jira.enabled = None
        jira.execution_url = None
        jira.summary_prefix = None
        jira.labels = None
        jira.comments = None
        jira.fix_version = None
        jira.build = None
        jira.only_if_changes = None
        jira.jira_tests_status.clear()

    @mock.patch('toolium.jira.logger')
    @requests_mock.Mocker()
    def test_change_jira_status(self, jira_logger, req_mock):
        # Test response
        response = b"The Test Case Execution 'TOOLIUM-2' has been created\r\n"

        # Configure jira module
        jira.enabled = True
        jira.execution_url = 'http://server/execution_service'
        jira.summary_prefix = 'prefix'
        jira.labels = 'label1 label2'
        jira.comments = 'comment'
        jira.fix_version = 'Release 1.0'
        jira.build = '453'
        jira.only_if_changes = True

        # Configure mock
        req_mock.get(jira.execution_url, content=response)

        # Test method
        jira.change_jira_status('TOOLIUM-1', 'Pass', None)

        # Check requested url
        for partial_url in [jira.execution_url, 'jiraStatus=Pass', 'jiraTestCaseId=TOOLIUM-1', 'summaryPrefix=prefix',
                            'labels=label1+label2', 'comments=comment', 'version=Release+1.0', 'build=453',
                            'onlyIfStatusChanges=true']:
            assert_in(partial_url, req_mock.request_history[0].url)

        # Check that binary response has been decoded
        expected_response = "Response content: The Test Case Execution 'TOOLIUM-2' has been created"
        jira_logger.debug.assert_called_with(expected_response)

    @mock.patch('toolium.jira.logger')
    @mock.patch('toolium.jira.requests.get')
    def test_change_jira_status_empty_url(self, jira_get, jira_logger):
        # Configure jira mock
        jira_get.side_effect = ConnectionError('exception error')

        # Configure jira module
        jira.enabled = True

        # Test method
        jira.change_jira_status('TOOLIUM-1', 'Pass', None)

        # Check logging error message
        expected_response = "Error updating Test Case 'TOOLIUM-1': execution_url is not configured"
        jira_logger.warn.assert_called_with(expected_response)

    @mock.patch('toolium.jira.logger')
    @mock.patch('toolium.jira.requests.get')
    def test_change_jira_status_exception(self, jira_get, jira_logger):
        # Configure jira mock
        jira_get.side_effect = ConnectionError('exception error')

        # Configure jira module
        jira.enabled = True
        jira.execution_url = 'http://server/execution_service'

        # Test method
        jira.change_jira_status('TOOLIUM-1', 'Pass', None)

        # Check logging error message
        expected_response = "Error updating Test Case 'TOOLIUM-1' using execution_url " \
                            "'http://server/execution_service': exception error"
        jira_logger.warn.assert_called_with(expected_response)

    def test_jira_annotation_pass(self):
        # Configure jira module
        config = DriverWrappersPool.get_default_wrapper().config
        try:
            config.add_section('Jira')
        except Exception:
            pass
        config.set('Jira', 'enabled', 'true')

        # Execute method with jira annotation
        MockTestClass().mock_test_pass()

        # Check jira status
        expected_status = {'TOOLIUM-1': ('TOOLIUM-1', 'Pass', None)}
        assert_equal(expected_status, jira.jira_tests_status)

    def test_jira_annotation_fail(self):
        # Configure jira module
        config = DriverWrappersPool.get_default_wrapper().config
        try:
            config.add_section('Jira')
        except Exception:
            pass
        config.set('Jira', 'enabled', 'true')

        # Execute method with jira annotation
        assert_raises(AssertionError, MockTestClass().mock_test_fail)

        # Check jira status
        expected_status = {'TOOLIUM-3': ('TOOLIUM-3', 'Fail', "The test 'test name' has failed: test error")}
        assert_equal(expected_status, jira.jira_tests_status)

    def test_jira_annotation_multiple(self):
        # Configure jira module
        config = DriverWrappersPool.get_default_wrapper().config
        try:
            config.add_section('Jira')
        except Exception:
            pass
        config.set('Jira', 'enabled', 'true')

        # Execute methods with jira annotation
        MockTestClass().mock_test_pass()
        assert_raises(AssertionError, MockTestClass().mock_test_fail)
        MockTestClass().mock_test_pass()

        # Check jira status
        expected_status = {'TOOLIUM-1': ('TOOLIUM-1', 'Pass', None),
                           'TOOLIUM-3': ('TOOLIUM-3', 'Fail', "The test 'test name' has failed: test error"),
                           'TOOLIUM-1': ('TOOLIUM-1', 'Pass', None)}
        assert_equal(expected_status, jira.jira_tests_status)

    def test_jira_disabled(self):
        # Configure jira module
        config = DriverWrappersPool.get_default_wrapper().config
        try:
            config.add_section('Jira')
        except Exception:
            pass
        config.set('Jira', 'enabled', 'false')

        # Execute method with jira annotation
        MockTestClass().mock_test_pass()

        # Check jira status
        expected_status = {}
        assert_equal(expected_status, jira.jira_tests_status)


class MockTestClass():
    def get_method_name(self):
        return 'test name'

    @jira.jira(test_key='TOOLIUM-1')
    def mock_test_pass(self):
        pass

    @jira.jira(test_key='TOOLIUM-3')
    def mock_test_fail(self):
        raise AssertionError('test error')
