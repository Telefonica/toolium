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
from requests.exceptions import ConnectionError

from toolium import jira


class JiraTests(unittest.TestCase):
    @requests_mock.Mocker()
    def test_change_jira_status(self, req_mock):
        # Test input
        execution_url = 'http://server/execution_service'
        response = b"The Test Case Execution 'TOOLIUM-2' has been created\r\n"

        # Configure mock
        jira.logger = mock.MagicMock()
        req_mock.get(execution_url, content=response)

        # Test method
        jira.change_jira_status(execution_url, test_key='TOOLIUM-1', test_status='Pass', summary_prefix='prefix',
                                labels='label1 label2', comments='comment',
                                fix_version='Release 1.0', build='453', only_if_changes=True)

        # Check requested url
        for partial_url in [execution_url, 'jiraStatus=Pass', 'jiraTestCaseId=TOOLIUM-1', 'summaryPrefix=prefix',
                            'labels=label1+label2', 'comments=comment', 'version=Release+1.0', 'build=453',
                            'onlyIfStatusChanges=true']:
            self.assertIn(partial_url, req_mock.request_history[0].url)

        # Check that binary response has been decoded
        expected_response = "Response content: The Test Case Execution 'TOOLIUM-2' has been created"
        jira.logger.debug.assert_called_with(expected_response)

    def test_change_jira_status_empty_url(self):
        # Configure mock
        jira.logger = mock.MagicMock()
        jira.requests.get = mock.MagicMock(side_effect=ConnectionError('exception error'))

        # Test method
        jira.change_jira_status('', 'TOOLIUM-1', 'Pass')

        # Check logging error message
        expected_response = "Error updating Test Case 'TOOLIUM-1': execution_url is not configured"
        jira.logger.warn.assert_called_with(expected_response)

    def test_change_jira_status_exception(self):
        # Configure mock
        jira.logger = mock.MagicMock()
        jira.requests.get = mock.MagicMock(side_effect=ConnectionError('exception error'))

        # Test method
        jira.change_jira_status('http://server/execution_service', 'TOOLIUM-1', 'Pass')

        # Check logging error message
        expected_response = "Error updating Test Case 'TOOLIUM-1' using execution_url " \
                            "'http://server/execution_service': exception error"
        jira.logger.warn.assert_called_with(expected_response)

    def test_jira_annotation_pass(self):
        # Execute method with jira annotation
        jira.jira_tests_status.clear()
        MockTestClass().mock_test_pass()

        # Check jira status
        expected_status = {'TOOLIUM-1': ('TOOLIUM-1', 'Pass', None)}
        self.assertEqual(expected_status, jira.jira_tests_status)

    def test_jira_annotation_fail(self):
        # Execute method with jira annotation
        jira.jira_tests_status.clear()
        self.assertRaises(AssertionError, MockTestClass().mock_test_fail)

        # Check jira status
        expected_status = {'TOOLIUM-3': ('TOOLIUM-3', 'Fail', "The test 'test name' has failed: test error")}
        self.assertEqual(expected_status, jira.jira_tests_status)

    def test_jira_annotation_multiple(self):
        # Execute methods with jira annotation
        jira.jira_tests_status.clear()
        MockTestClass().mock_test_pass()
        self.assertRaises(AssertionError, MockTestClass().mock_test_fail)
        MockTestClass().mock_test_pass()

        # Check jira status
        expected_status = {'TOOLIUM-1': ('TOOLIUM-1', 'Pass', None),
                           'TOOLIUM-3': ('TOOLIUM-3', 'Fail', "The test 'test name' has failed: test error"),
                           'TOOLIUM-1': ('TOOLIUM-1', 'Pass', None)}
        self.assertEqual(expected_status, jira.jira_tests_status)


class MockTestClass():
    def get_method_name(self):
        return 'test name'

    @jira.jira(test_key='TOOLIUM-1')
    def mock_test_pass(self):
        pass

    @jira.jira(test_key='TOOLIUM-3')
    def mock_test_fail(self):
        raise AssertionError('test error')
