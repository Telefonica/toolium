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

import logging

import requests

from toolium.config_driver import get_error_message_from_exception
from toolium.driver_wrappers_pool import DriverWrappersPool

# Dict to save tuples with jira keys, their test status and comments
jira_tests_status = {}

# Jira configuration
enabled = None
execution_url = None
summary_prefix = None
labels = None
comments = None
fix_version = None
build = None
only_if_changes = None

logger = logging.getLogger(__name__)


def jira(test_key):
    """Decorator to update test status in Jira

    :param test_key: test case key in Jira
    :returns: jira test
    """

    def decorator(test_item):
        def modified_test(*args, **kwargs):
            save_jira_conf()
            try:
                test_item(*args, **kwargs)
            except Exception as e:
                error_message = get_error_message_from_exception(e)
                test_comment = "The test '{}' has failed: {}".format(args[0].get_method_name(), error_message)
                add_jira_status(test_key, 'Fail', test_comment)
                raise
            add_jira_status(test_key, 'Pass', None)

        modified_test.__name__ = test_item.__name__
        return modified_test

    return decorator


def save_jira_conf():
    """Read Jira configuration from properties file and save it"""
    global enabled, execution_url, summary_prefix, labels, comments, fix_version, build, only_if_changes
    config = DriverWrappersPool.get_default_wrapper().config
    enabled = config.getboolean_optional('Jira', 'enabled')
    execution_url = config.get_optional('Jira', 'execution_url')
    summary_prefix = config.get_optional('Jira', 'summary_prefix')
    labels = config.get_optional('Jira', 'labels')
    comments = config.get_optional('Jira', 'comments')
    fix_version = config.get_optional('Jira', 'fixversion')
    build = config.get_optional('Jira', 'build')
    only_if_changes = config.getboolean_optional('Jira', 'onlyifchanges')


def add_jira_status(test_key, test_status, test_comment):
    """Save test status and comments to update Jira later

    :param test_key: test case key in Jira
    :param test_status: test case status
    :param test_comment: test case comments
    """
    if test_key and enabled:
        if test_status == 'Fail':
            if test_key in jira_tests_status and jira_tests_status[test_key][2]:
                test_comment = '{}\n{}'.format(jira_tests_status[test_key][2], test_comment)
            jira_tests_status[test_key] = (test_key, 'Fail', test_comment)
        elif test_status == 'Pass':
            # Don't overwrite previous fails
            if test_key not in jira_tests_status:
                jira_tests_status[test_key] = (test_key, 'Pass', test_comment)


def change_all_jira_status():
    """Iterate over all jira test cases, update their status in Jira and clear the dictionary"""
    for test_status in jira_tests_status.values():
        change_jira_status(*test_status)
    jira_tests_status.clear()


def change_jira_status(test_key, test_status, test_comment):
    """Update test status in Jira

    :param test_key: test case key in Jira
    :param test_status: test case status
    :param test_comment: test case comments
    """
    logger.info("Updating Test Case '{0}' in Jira with status {1}".format(test_key, test_status))
    composed_comments = comments
    if test_comment:
        composed_comments = '{}\n{}'.format(comments, test_comment) if comments else test_comment
    payload = {'jiraTestCaseId': test_key, 'jiraStatus': test_status, 'summaryPrefix': summary_prefix,
               'labels': labels, 'comments': composed_comments, 'version': fix_version, 'build': build}
    if only_if_changes:
        payload['onlyIfStatusChanges'] = 'true'
    try:
        response = requests.get(execution_url, params=payload)
    except Exception as e:
        if execution_url:
            logger.warn("Error updating Test Case '{}' using execution_url '{}': {}".format(test_key, execution_url, e))
        else:
            logger.warn("Error updating Test Case '{}': execution_url is not configured".format(test_key))
        return

    logger.debug("Request url: {}".format(response.url))
    if response.status_code >= 400:
        logger.warn("Error updating Test Case '{}': [{}] {}".format(test_key, response.status_code, response.content))
    else:
        logger.debug("Response content: {}".format(response.content.decode().splitlines()[0]))
