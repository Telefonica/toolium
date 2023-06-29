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
import importlib
import os
import unittest
from tempfile import TemporaryFile
from unittest.mock import ANY
import mock
import pytest
from jira import JIRAError
from jira.resources import Version
from requests.exceptions import ConnectionError

import toolium
from toolium import jira
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.jira import JiraServer, _check_fix_version


@pytest.fixture
def logger():
    # Configure logger mock
    logger = mock.MagicMock()
    logger_patch = mock.patch('logging.getLogger', mock.MagicMock(return_value=logger))
    logger_patch.start()

    yield logger

    logger_patch.stop()

    # Clear jira module configuration
    importlib.reload(toolium.jira)

def test_change_jira_status(logger):

    # Configure jira module
    jira.enabled = True
    jira.execution_url = 'http://server/execution_service'
    jira.logger = mock.MagicMock()
    jira.check_jira_args = mock.MagicMock()
    jira.add_results = mock.MagicMock()
    jira.transition = mock.MagicMock()
    jira.execute_query = mock.MagicMock()
    jira.execute_query.return_value = [mock.MagicMock()]
    def create_test(*args, **kwargs):
        mock_test = mock.MagicMock(key="TOOLIUM-TEST")
        return mock_test
    jira.create_test_execution = create_test

    # Test method
    jira.change_jira_status('TOOLIUM-1', 'Pass', None, [], mock.MagicMock())

    # Check logging call
    jira.logger.debug.assert_any_call("Creating execution for TOOLIUM-1")
    jira.logger.info.assert_called_with(f"Created execution TOOLIUM-TEST for test TOOLIUM-1")


def test_change_jira_status_attachments(logger):

    # Configure jira module
    jira.enabled = True
    jira.execution_url = 'http://server/execution_service'
    jira.only_if_changes = True
    attachments = [os.path.dirname(TemporaryFile().name)]
    jira.logger = mock.MagicMock()
    def addlogs(*args, **kwargs):
        jira.logger.info("Attached log into TOOLIUM-1")
    jira._addlogs = addlogs

    # Test method
    jira.add_results(mock.MagicMock(), 'TOOLIUM-1', attachments)

    # Check logging call
    calls = [mock.call('Adding results to issue...'),
             mock.call('Screenshots uploaded...'),
             mock.call("Attached log into TOOLIUM-1")]
    jira.logger.info.assert_has_calls(calls)


@mock.patch('toolium.jira.requests.get')
def test_change_jira_status_empty_url(jira_get, logger):
    # Configure jira mock
    jira_get.side_effect = ConnectionError('exception error')

    # Configure jira module
    jira.enabled = True
    jira.logger = mock.MagicMock()

    # Test method
    jira.change_jira_status('TOOLIUM-1', 'Pass', None, [])

    # Check logging error message
    jira.logger.warning.assert_called_once_with("Test Case '%s' can not be updated: execution_url is not configured",
                                           'TOOLIUM-1')


@mock.patch('toolium.jira.requests.post')
def test_change_jira_status_exception(jira_post, logger):
    # Configure jira mock
    jira_post.side_effect = ConnectionError()

    # Configure jira module
    jira.enabled = True
    jira.execution_url = 'http://server/execution_service'
    jira.logger = mock.MagicMock()

    # Test method
    jira.change_jira_status('TOOLIUM-1', 'Pass', None, [])

    # Check logging error message
    jira.logger.error.assert_called_with("Exception while updating Issue '%s': %s", 'TOOLIUM-1', ANY)


def test_jira_annotation_pass(logger):
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
    expected_status = {'TOOLIUM-1': ('TOOLIUM-1', 'Pass', None, [])}
    assert expected_status == jira.jira_tests_status


def test_jira_annotation_fail(logger):
    # Configure jira module
    config = DriverWrappersPool.get_default_wrapper().config
    try:
        config.add_section('Jira')
    except Exception:
        pass
    config.set('Jira', 'enabled', 'true')

    # Execute method with jira annotation
    with pytest.raises(AssertionError):
        MockTestClass().mock_test_fail()

    # Check jira status
    expected_status = {'TOOLIUM-3': ('TOOLIUM-3', 'Fail', "The test 'test name' has failed: test error", [])}
    assert expected_status == jira.jira_tests_status


def test_jira_annotation_multiple(logger):
    # Configure jira module
    config = DriverWrappersPool.get_default_wrapper().config
    try:
        config.add_section('Jira')
    except Exception:
        pass
    config.set('Jira', 'enabled', 'true')

    # Execute methods with jira annotation
    MockTestClass().mock_test_pass()
    with pytest.raises(AssertionError):
        MockTestClass().mock_test_fail()
    MockTestClass().mock_test_pass_2()

    # Check jira status
    expected_status = {'TOOLIUM-1': ('TOOLIUM-1', 'Pass', None, []),
                       'TOOLIUM-3': ('TOOLIUM-3', 'Fail', "The test 'test name' has failed: test error", []),
                       'TOOLIUM-2': ('TOOLIUM-2', 'Pass', None, [])}
    assert expected_status == jira.jira_tests_status


def test_jira_disabled(logger):
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
    assert expected_status == jira.jira_tests_status


class MockTestClass():
    def get_method_name(self):
        return 'test name'

    @jira.jira(test_key='TOOLIUM-1')
    def mock_test_pass(self):
        pass

    @jira.jira(test_key='TOOLIUM-2')
    def mock_test_pass_2(self):
        pass

    @jira.jira(test_key='TOOLIUM-3')
    def mock_test_fail(self):
        raise AssertionError('test error')


def test_jira_connection_anonymous():
    with JiraServer("https://issues.apache.org/jira", None) as jira:
        assert len(jira.projects()) > 1


@unittest.skip("TOKEN injection pending")
def test_jira_connection_private_user():
    def call_jira_server():
        with JiraServer("https://issues.apache.org/jira", "") as jira:  # TODO
            assert jira.current_user()
    unittest.TestCase().assertRaises(JIRAError, call_jira_server)


def test_jira_connection_invalid_url():
    # with JiraServer("http://github.com", None) as jira:
    #     return
    def call_jira_server():
        with JiraServer("http://github.com", None):
            return
    unittest.TestCase().assertRaisesRegex(JIRAError, "^JiraError HTTP 406 url",  call_jira_server)


def test_jira_connection_invalid_token():
    def call_jira_server():
        with JiraServer("https://jira.elevenpaths.com/", "6") as jira:
            assert jira.current_user()
    unittest.TestCase().assertRaises(JIRAError, call_jira_server)


def test_jira_check_valid_fix_version():
    version = mock.Mock(Version)
    version.configure_mock(raw={"name": "1.1"})
    server = mock.Mock(JiraServer("https://jira.elevenpaths.com/", "6"))
    server.configure_mock(project=lambda x: "KEY", project_versions=lambda arg: [version])
    _check_fix_version(server, "KEY", "1.1")


def test_jira_check_wrong_fix_version():
    version = mock.Mock(Version)
    version.configure_mock(raw={"name": "0.5"})
    server = mock.Mock(JiraServer("https://jira.elevenpaths.com/", "6"))
    server.configure_mock(project=lambda x: "KEY", project_versions=lambda arg: [version])

    def call_check_fix_version_wrong():
        _check_fix_version(server, "KEY", "1.1")
    unittest.TestCase().assertRaisesRegex(ValueError,
                                          "No existe la fix version '1.1'",
                                          call_check_fix_version_wrong)
