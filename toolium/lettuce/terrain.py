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

from lettuce import before, after, world  # @UnresolvedImport

from toolium import toolium_wrapper
from toolium.driver_wrapper import DriverWrappersPool
from toolium.jira import add_jira_status, change_all_jira_status
from toolium.visual_test import VisualTest


@before.each_scenario
def setup_driver(scenario):
    # Configure logger
    world.logger = logging.getLogger()

    # Create driver
    if not hasattr(world, 'driver') or not world.driver:
        toolium_wrapper.configure()
        world.driver = toolium_wrapper.connect()
        world.utils = toolium_wrapper.utils

    # Configure visual tests
    def assertScreenshot(element_or_selector, filename, threshold=0, exclude_element=None, driver_wrapper=None):
        file_suffix = scenario.name.replace(' ', '_')
        VisualTest(driver_wrapper).assertScreenshot(element_or_selector, filename, file_suffix, threshold,
                                                    exclude_element)

    def assertFullScreenshot(filename, threshold=0, exclude_elements=[], driver_wrapper=None):
        file_suffix = scenario.name.replace(' ', '_')
        VisualTest(driver_wrapper).assertScreenshot(None, filename, file_suffix, threshold, exclude_elements)

    world.assertScreenshot = assertScreenshot
    world.assertFullScreenshot = assertFullScreenshot

    # Add implicitly wait
    implicitly_wait = toolium_wrapper.config.get_optional('Common', 'implicitly_wait')
    if implicitly_wait:
        world.driver.implicitly_wait(implicitly_wait)

    world.logger.info("Running new scenario: {0}".format(scenario.name))


@after.each_scenario
def teardown_driver(scenario):
    # Get scenario name without spaces
    scenario_file_name = scenario.name.replace(' ', '_')

    # Check test result
    if scenario.failed:
        # TODO: never enters here in scenarios with datasets
        test_status = 'Fail'
        test_comment = "The scenario '{0}' has failed".format(scenario.name)
        DriverWrappersPool.capture_screenshots(scenario_file_name)
        world.logger.error(test_comment)
    else:
        test_status = 'Pass'
        test_comment = None
        world.logger.info("The scenario '{0}' has passed".format(scenario.name))

    # Close browser and stop driver
    reuse_driver = toolium_wrapper.config.getboolean_optional('Common', 'reuse_driver')
    if not reuse_driver:
        DriverWrappersPool.close_drivers()
        DriverWrappersPool.download_videos(scenario_file_name, not scenario.failed)

    # Save test status to be updated later
    test_key = get_jira_key_from_scenario(scenario)
    if test_key:
        add_jira_status(test_key, test_status, test_comment)


@after.all
def teardown_driver_all(total):
    if hasattr(world, 'driver') and world.driver:
        DriverWrappersPool.close_drivers()
        DriverWrappersPool.download_videos('multiple_tests')
    # Update tests status in Jira
    change_all_jira_status()


def get_jira_key_from_scenario(scenario):
    """Extract Jira Test Case key from scenario tags

    :param scenario: lettuce scenario
    :returns: Jira test case key
    """
    jira_regex = re.compile('jira\(\'(.*?)\'\)')
    for tag in scenario.tags:
        match = jira_regex.search(tag)
        if match:
            return match.group(1)
    return None
