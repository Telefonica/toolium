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
import re

from toolium import toolium_wrapper
from toolium.jira import add_jira_status, change_all_jira_status
from toolium.utils import Utils
from toolium.visual_test import VisualTest


def before_all(context):
    """Initialization method that will be executed before the test execution

    :param context: behave context
    """
    # Configure logger
    context.logger = logging.getLogger()

    # Create driver if it must be reused
    toolium_wrapper.configure()
    context.reuse_driver = toolium_wrapper.config.getboolean_optional('Common', 'reuse_driver')
    if context.reuse_driver:
        context.driver = toolium_wrapper.connect()
        context.utils = Utils(toolium_wrapper)
        context.remote_video_node = context.utils.get_remote_video_node()


def before_scenario(context, scenario):
    """Scenario initialization

    :param context: behave context
    :param scenario: running scenario
    """
    # Create driver if it must not be reused
    if not context.reuse_driver:
        toolium_wrapper.configure()
        context.driver = toolium_wrapper.connect()
        context.utils = Utils(toolium_wrapper)
        context.remote_video_node = context.utils.get_remote_video_node()

    # Configure visual tests
    def assertScreenshot(element_or_selector, filename, threshold=0, exclude_element=None, driver_wrapper=None):
        file_suffix = scenario.name.replace(' ', '_')
        VisualTest(driver_wrapper).assertScreenshot(element_or_selector, filename, file_suffix, threshold,
                                                    exclude_element)

    def assertFullScreenshot(filename, threshold=0, exclude_elements=[], driver_wrapper=None):
        file_suffix = scenario.name.replace(' ', '_')
        VisualTest(driver_wrapper).assertScreenshot(None, filename, file_suffix, threshold, exclude_elements)

    context.assertScreenshot = assertScreenshot
    context.assertFullScreenshot = assertFullScreenshot

    # Add implicitly wait
    implicitly_wait = toolium_wrapper.config.get_optional('Common', 'implicitly_wait')
    if implicitly_wait:
        context.driver.implicitly_wait(implicitly_wait)

    context.logger.info("Running new scenario: {0}".format(scenario.name))


def after_scenario(context, scenario):
    """Clean method that will be executed after each scenario

    :param context: behave context
    :param scenario: running scenario
    """
    # Check test result
    flag_failed = scenario.status != 'passed'

    if flag_failed:
        test_status = 'Fail'
        test_comment = "The scenario '{0}' has failed".format(scenario.name)
        context.utils.capture_screenshot(scenario.name.replace(' -- @', '_').replace(' ', '_'))
        context.logger.error(test_comment)
    else:
        test_status = 'Pass'
        test_comment = None
        context.logger.info("The scenario '{0}' has passed".format(scenario.name))

    # Close browser and stop driver if it must not be reused
    if not context.reuse_driver:
        finalize_driver(context, scenario.name.replace(' ', '_'), not flag_failed)

    # Save test status to be updated later
    test_key = get_jira_key_from_scenario(scenario)
    if test_key:
        add_jira_status(test_key, test_status, test_comment)


def after_all(context):
    """Clean method that will be executed after all features are finished

    :param context: behave context
    """
    # Close browser and stop driver if it has been reused
    if context.reuse_driver:
        finalize_driver(context, 'multiple_tests')
    # Update tests status in Jira
    change_all_jira_status()


def finalize_driver(context, video_name, test_passed=True):
    """Close browser, stop driver and download test video

    :param context: behave context
    :param video_name: video name
    :param test_passed: test execution status
    """
    # Get session id to request the saved video
    session_id = context.driver.session_id

    # Close browser and stop driver
    context.driver.quit()

    # Download saved video if video is enabled or if test fails
    if context.remote_video_node and (toolium_wrapper.config.getboolean_optional('Server', 'video_enabled')
                                      or not test_passed):
        video_name = video_name if test_passed else 'error_{}'.format(video_name)
        context.utils.download_remote_video(context.remote_video_node, session_id, video_name)


def get_jira_key_from_scenario(scenario):
    """Extract Jira Test Case key from scenario tags

    :param scenario: behave scenario
    :returns: Jira test case key
    """
    jira_regex = re.compile('jira\(\'(.*?)\'\)')
    for tag in scenario.tags:
        match = jira_regex.search(tag)
        if match:
            return match.group(1)
    return None
