# -*- coding: utf-8 -*-

u"""
(c) Copyright 2014 Telefónica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefónica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefónica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
"""

import logging

import requests

from toolium import selenium_driver
from toolium.config_driver import get_error_message_from_exception

"""Configuration"""
logger = logging.getLogger(__name__)
# Base url of the test execution service
JIRA_EXECUTION_URL = 'http://qacore02.hi.inet/jira/test-case-execution'
# Dict to save tuples with jira keys, their test status and comments
jira_tests_status = {}


def jira(test_key):
    """Decorator to update test status in Jira

    :param test_key: test case key in Jira
    :returns: jira test
    """

    def decorator(test_item):
        def modified_test(*args, **kwargs):
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


def add_jira_status(test_key, test_status, test_comment):
    """Save test status and comments to update Jira later

    :param test_key: test case key in Jira
    :param test_status: test case status
    :param test_comment: test case comments
    """
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
    for test_status in jira_tests_status.itervalues():
        change_jira_status_with_config(*test_status)
    jira_tests_status.clear()


def change_jira_status_with_config(test_key, test_status, test_comment):
    """Read Jira configuration properties and update test status in Jira

    :param test_key: test case key in Jira
    :param test_status: test case status
    :param test_comment: test case comments
    """
    config = selenium_driver.config
    if config.getboolean_optional('Jira', 'enabled'):
        summary_prefix = config.get_optional('Jira', 'summary_prefix')
        labels = config.get_optional('Jira', 'labels')
        comments = config.get_optional('Jira', 'comments')
        if test_comment:
            comments = '{}\n{}'.format(comments, test_comment) if comments else test_comment
        fix_version = config.get_optional('Jira', 'fixversion')
        build = config.get_optional('Jira', 'build')
        only_if_changes = config.getboolean_optional('Jira', 'onlyifchanges')
        change_jira_status(test_key, test_status, summary_prefix, labels, comments, fix_version, build, only_if_changes)


def change_jira_status(test_key, test_status, summary_prefix=None, labels=None, comments=None, fix_version=None,
                       build=None, only_if_changes=False):
    """Update test status in Jira

    :param test_key: test case key in Jira
    :param test_status: test case status
    :param summary_prefix: test case summary prefix
    :param labels: test case labels
    :param comments: test case comments
    :param fix_version: test case fix version
    :param build: test case build
    :param only_if_changes:
        if true, only create a new execution if the test status has changed
        if false, create a new execution always
    """
    logger.info("Updating Test Case '{0}' in Jira with status {1}".format(test_key, test_status))
    payload = {'jiraTestCaseId': test_key, 'jiraStatus': test_status, 'summaryPrefix': summary_prefix, 'labels': labels, 'comments': comments,
               'version': fix_version, 'build': build}
    if only_if_changes:
        payload['onlyIfStatusChanges'] = 'true'
    response = requests.get(JIRA_EXECUTION_URL, params=payload)
    logger.debug("Request url: {}".format(response.url))
    if response.status_code >= 400:
        logger.warn("Error updating Test Case '{}': [{}] {}".format(test_key, response.status_code, response.content))
    else:
        logger.debug("Response content: {}".format(response.content))
