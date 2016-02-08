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
from toolium.jira import add_jira_status, change_all_jira_status, save_jira_conf
from toolium.visual_test import VisualTest


def before_all(context):
    """Initialization method that will be executed before the test execution

    :param context: behave context
    """
    # Configure logger
    context.logger = logging.getLogger()

    # Get default driver wrapper
    context.driver_wrapper = DriverWrappersPool.get_default_wrapper()

    # Configure wrapper
    if not hasattr(context, 'config_files'):
        context.config_files = ConfigFiles()
    context.driver_wrapper.configure(True, context.config_files)
    context.toolium_config = context.driver_wrapper.config

    # Create driver if it must be reused
    context.reuse_driver = context.driver_wrapper.config.getboolean_optional('Common', 'reuse_driver')
    if context.reuse_driver:
        context.driver = context.driver_wrapper.connect()
        context.utils = context.driver_wrapper.utils


def before_scenario(context, scenario):
    """Scenario initialization

    :param context: behave context
    :param scenario: running scenario
    """
    # Get default driver wrapper
    context.driver_wrapper = DriverWrappersPool.get_default_wrapper()

    # Create driver if it must not be reused
    if not context.reuse_driver:
        # Configure wrapper
        context.driver_wrapper.configure(True, context.config_files)
        context.toolium_config = context.driver_wrapper.config

        # Create driver
        context.driver = context.driver_wrapper.connect()
        context.utils = context.driver_wrapper.utils

    # Common initialization
    bdd_common_before_scenario(context, scenario, context.driver_wrapper)


def bdd_common_before_scenario(context_or_world, scenario, driver_wrapper):
    """Common scenario initialization in behave or lettuce

    :param context_or_world: behave context or lettuce world
    :param scenario: running scenario
    :param driver_wrapper: driver wrapper instance
    """

    def assert_screenshot(element_or_selector, filename, threshold=0, exclude_elements=[], driver_wrapper=None):
        file_suffix = scenario.name.replace(' ', '_')
        VisualTest(driver_wrapper).assert_screenshot(element_or_selector, filename, file_suffix, threshold,
                                                     exclude_elements)

    def assert_full_screenshot(filename, threshold=0, exclude_elements=[], driver_wrapper=None):
        file_suffix = scenario.name.replace(' ', '_')
        VisualTest(driver_wrapper).assert_screenshot(None, filename, file_suffix, threshold, exclude_elements)

    context_or_world.assert_screenshot = assert_screenshot
    context_or_world.assert_full_screenshot = assert_full_screenshot
    context_or_world.app_strings = driver_wrapper.app_strings

    # Save Jira conf
    save_jira_conf()

    # Add implicitly wait
    implicitly_wait = driver_wrapper.config.get_optional('Common', 'implicitly_wait')
    if implicitly_wait:
        context_or_world.driver.implicitly_wait(implicitly_wait)

    context_or_world.logger.info("Running new scenario: {0}".format(scenario.name))


def after_scenario(context, scenario):
    """Clean method that will be executed after each scenario

    :param context: behave context
    :param scenario: running scenario
    """
    bdd_common_after_scenario(context, scenario, scenario.status)


def bdd_common_after_scenario(context_or_world, scenario, status):
    """Clean method that will be executed after each scenario in behave or lettuce

    :param context_or_world: behave context or lettuce world
    :param scenario: running scenario
    :param status: scenario status (passed, failed or skipped)
    """
    # Get scenario name without spaces and behave data separator
    scenario_file_name = scenario.name.replace(' -- @', '_').replace(' ', '_')

    if status == 'skipped':
        return
    elif status == 'passed':
        test_status = 'Pass'
        test_comment = None
        context_or_world.logger.info("The scenario '{0}' has passed".format(scenario.name))
    else:
        test_status = 'Fail'
        test_comment = "The scenario '{0}' has failed".format(scenario.name)
        DriverWrappersPool.capture_screenshots(scenario_file_name)
        context_or_world.logger.error(test_comment)

    # Close browser and stop driver if it must not be reused
    DriverWrappersPool.close_drivers_and_download_videos(scenario_file_name, status == 'passed',
                                                         context_or_world.reuse_driver)

    # Save test status to be updated later
    add_jira_status(get_jira_key_from_scenario(scenario), test_status, test_comment)


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
    """Extract Jira Test Case key from scenario tags.
    Two tag formats are allowed:
    @jira('PROJECT-32')
    @jira=PROJECT-32

    :param scenario: behave scenario
    :returns: Jira test case key
    """
    jira_regex = re.compile('jira[=\(\']*([A-Z]+\-[0-9]+)[\'\)]*$')
    for tag in scenario.tags:
        match = jira_regex.search(tag)
        if match:
            return match.group(1)
    return None
