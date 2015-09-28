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
import re

from lettuce import before, after, world  # @UnresolvedImport
from toolium import toolium_driver
from toolium.utils import Utils
from toolium.jira import add_jira_status, change_all_jira_status
from toolium.visual_test import VisualTest


@before.each_scenario
def setup_driver(scenario):
    # Configure logger
    world.logger = logging.getLogger()
    # Create driver
    if not hasattr(world, 'driver') or not world.driver:
        toolium_driver.configure()
        world.driver = toolium_driver.connect()
        world.utils = Utils(world.driver)
        world.remote_video_node = world.utils.get_remote_video_node()

    # Configure visual tests
    def assertScreenshot(element_or_selector, filename, threshold=0, exclude_element=None):
        file_suffix = scenario.name.replace(' ', '_')
        VisualTest().assertScreenshot(element_or_selector, filename, file_suffix, threshold, exclude_element)

    world.assertScreenshot = assertScreenshot

    # Add implicitly wait
    implicitly_wait = toolium_driver.config.get_optional('Common', 'implicitly_wait')
    if (implicitly_wait):
        world.driver.implicitly_wait(implicitly_wait)
    # Maximize browser
    if toolium_driver.is_maximizable():
        world.driver.maximize_window()


@after.each_scenario
def teardown_driver(scenario):
    # Check test result
    if scenario.failed:
        # TODO: never enters here in scenarios with datasets
        test_status = 'Fail'
        print dir(scenario)
        test_comment = "The scenario '{}' has failed: {}".format(scenario.name, None)
        world.utils.capture_screenshot(scenario.name.replace(' ', '_'))
    else:
        test_status = 'Pass'
        test_comment = None

    # Close browser and stop driver
    reuse_driver = toolium_driver.config.getboolean_optional('Common', 'reuse_driver')
    if not reuse_driver:
        finalize_driver(scenario.name.replace(' ', '_'), not scenario.failed)

    # Save test status to be updated later
    test_key = get_jira_key_from_scenario(scenario)
    add_jira_status(test_key, test_status, test_comment)


@after.all
def teardown_driver_all(total):
    if hasattr(world, 'driver') and world.driver:
        finalize_driver('multiple_tests')
    # Update tests status in Jira
    change_all_jira_status()


def finalize_driver(video_name, test_passed=True):
    """Close browser, stop driver and download test video

    :param video_name: video name
    :param test_passed: test execution status
    """
    # Get session id to request the saved video
    session_id = world.driver.session_id

    # Close browser and stop driver
    world.driver.quit()
    world.driver = None

    # Download saved video if video is enabled or if test fails
    if world.remote_video_node and (toolium_driver.config.getboolean_optional('Server', 'video_enabled')
                                    or not test_passed):
        video_name = video_name if test_passed else 'error_{}'.format(video_name)
        world.utils.download_remote_video(world.remote_video_node, session_id, video_name)


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
