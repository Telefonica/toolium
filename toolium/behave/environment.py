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

from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrappersPool
from toolium.jira import add_jira_status, change_all_jira_status
from toolium.visual_test import VisualTest


def before_all(context):
    """Initialization method that will be executed before the test execution

    :param context: behave context
    """
    # Configure logger
    context.logger = logging.getLogger()

    # Get default driver wrapper
    wrapper = DriverWrappersPool.get_default_wrapper()

    # Configure wrapper
    if not hasattr(context, 'config_files'):
        context.config_files = ConfigFiles()
    wrapper.configure(True, context.config_files)

    # Create driver if it must be reused
    context.reuse_driver = wrapper.config.getboolean_optional('Common', 'reuse_driver')
    if context.reuse_driver:
        context.driver = wrapper.connect()
        context.utils = wrapper.utils


def before_scenario(context, scenario):
    """Scenario initialization

    :param context: behave context
    :param scenario: running scenario
    """
    # Get default driver wrapper
    wrapper = DriverWrappersPool.get_default_wrapper()

    # Create driver if it must not be reused
    if not context.reuse_driver:
        # Configure wrapper
        wrapper.configure(True, context.config_files)

        # Create driver
        context.driver = wrapper.connect()
        context.utils = wrapper.utils

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
    implicitly_wait = wrapper.config.get_optional('Common', 'implicitly_wait')
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

    # Get scenario name without spaces and behave data separator
    scenario_file_name = scenario.name.replace(' -- @', '_').replace(' ', '_')

    if flag_failed:
        test_status = 'Fail'
        test_comment = "The scenario '{0}' has failed".format(scenario.name)
        DriverWrappersPool.capture_screenshots(scenario_file_name)
        context.logger.error(test_comment)
    else:
        test_status = 'Pass'
        test_comment = None
        context.logger.info("The scenario '{0}' has passed".format(scenario.name))

    # Close browser and stop driver if it must not be reused
    DriverWrappersPool.close_drivers_and_download_videos(scenario_file_name, not flag_failed, context.reuse_driver)

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
        DriverWrappersPool.close_drivers_and_download_videos('multiple_tests')
    # Update tests status in Jira
    change_all_jira_status()


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
