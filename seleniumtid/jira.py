# -*- coding: utf-8 -*-
'''
(c) Copyright 2014 Telefonica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefonica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefonica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
'''
import logging
import urllib
import urllib2
import re
from seleniumtid import selenium_driver
from seleniumtid.config_driver import get_error_message_from_exception

# Configure logger
logger = logging.getLogger(__name__)

# Base url of the test execution service
JIRA_EXECUTION_URL = 'http://qacore02.hi.inet/jira/test-case-execution'

# Dict to save tuples with jira keys, their test status and comments
jira_tests_status = {}


def jira(test_key):
    '''
    Decorator to update test status in Jira
    '''
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
        return modified_test
    return decorator


def add_jira_status(test_key, test_status, test_comment):
    '''
    Save test status and comments to update Jira later
    '''
    if test_status == 'Fail':
        if test_key in jira_tests_status and jira_tests_status[test_key][2]:
            test_comment = '{}\n{}'.format(jira_tests_status[test_key][2], test_comment)
        jira_tests_status[test_key] = (test_key, 'Fail', test_comment)
    elif test_status == 'Pass':
        # Don't overwrite previous fails
        if test_key not in jira_tests_status:
            jira_tests_status[test_key] = (test_key, 'Pass', test_comment)


def change_all_jira_status():
    '''
    Iterate over all jira test cases, update their status in Jira and clear the dictionary
    '''
    for test_status in jira_tests_status.itervalues():
        change_jira_status_with_config(*test_status)
    jira_tests_status.clear()


def change_jira_status_with_config(test_key, test_status, test_comment):
    '''
    Read Jira configuration properties and update test status in Jira
    '''
    config = selenium_driver.config
    if config.getboolean_optional('Jira', 'enabled'):
        labels = config.get_optional('Jira', 'labels')
        comments = config.get_optional('Jira', 'comments')
        if test_comment:
            comments = '{}\n{}'.format(comments, test_comment) if comments else test_comment
        fixversion = config.get_optional('Jira', 'fixversion')
        build = config.get_optional('Jira', 'build')
        onlyifchanges = config.getboolean_optional('Jira', 'onlyifchanges')
        change_jira_status(test_key, test_status, labels, comments, fixversion, build, onlyifchanges)


def change_jira_status(test_key, test_status, labels=None, comments=None, fixversion=None, build=None,
                       onlyifchanges=False):
    '''
    Update test status in Jira
    '''
    logger.info("Updating Test Case '{0}' in Jira with status {1}".format(test_key, test_status))
    jira_execution_url = '{0}?jiraTestCaseId={1}&jiraStatus={2}'.format(JIRA_EXECUTION_URL, test_key, test_status)
    if labels:
        jira_execution_url += '&labels={0}'.format(urllib.quote(labels))
    if comments:
        jira_execution_url += '&comments={0}'.format(urllib.quote(comments))
    if fixversion:
        jira_execution_url += '&version={0}'.format(urllib.quote(fixversion))
    if build:
        jira_execution_url += '&build={0}'.format(urllib.quote(build))
    if onlyifchanges:
        jira_execution_url += '&onlyIfStatusChanges=true'

    try:
        response = urllib2.urlopen(jira_execution_url)
        logger.debug(response.read().strip(' \t\n\r'))
        response.close()
    except urllib2.HTTPError as exc:
        # Extract error message from the HTTP response
        message = re.search('.*<u>(.*)</u></p><p>.*', exc.read())
        if message:
            error_message = message.group(1)
        else:
            message = re.search('.*<title>(.*)</title>.*', exc.read())
            if message:
                error_message = message.group(1)
        logger.warn("Error updating Test Case '{0}': [{1}] {2}".format(test_key, exc.code, error_message))
    except urllib2.URLError as exc:
        logger.warn("Error updating Test Case '{0}': {1}".format(test_key, exc.reason))
