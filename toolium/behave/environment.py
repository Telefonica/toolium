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
import os
import re

try:
    from behave_pytest.hook import install_pytest_asserts
except ImportError:
    def install_pytest_asserts():
        pass

from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrappersPool
from toolium.jira import add_jira_status, change_all_jira_status, save_jira_conf
from toolium.visual_test import VisualTest


def before_all(context):
    """Initialization method that will be executed before the test execution

    :param context: behave context
    """
    # Use pytest asserts if behave_pytest is installed
    install_pytest_asserts()

    if not hasattr(context, 'config_files'):
        context.config_files = ConfigFiles()

    # By default config directory is located in environment path
    if not context.config_files.config_directory:
        context.config_files.set_config_directory(DriverWrappersPool.get_default_config_directory())

    # Get 'Config_environment' property from user input (e.g. -D Config_environment=ios)
    env = context.config.userdata.get('Config_environment')
    # Deprecated: Get 'env' property from user input (e.g. -D env=ios)
    env = env if env else context.config.userdata.get('env')
    if env:
        os.environ['Config_environment'] = env

    context.global_status = {'test_passed': True}
    create_and_configure_wrapper(context)


def before_scenario(context, scenario):
    """Scenario initialization

    :param context: behave context
    :param scenario: running scenario
    """
    # Configure reset properties from behave tags
    if 'no_reset_app' in scenario.tags:
        os.environ["AppiumCapabilities_noReset"] = 'true'
        os.environ["AppiumCapabilities_fullReset"] = 'false'
    elif 'reset_app' in scenario.tags:
        os.environ["AppiumCapabilities_noReset"] = 'false'
        os.environ["AppiumCapabilities_fullReset"] = 'false'
    elif 'full_reset_app' in scenario.tags:
        os.environ["AppiumCapabilities_noReset"] = 'false'
        os.environ["AppiumCapabilities_fullReset"] = 'true'

    # Skip android_only or ios_only scenarios
    if 'android_only' in scenario.tags and context.driver_wrapper.is_ios_test():
        scenario.skip('Android scenario')
        return
    elif 'ios_only' in scenario.tags and context.driver_wrapper.is_android_test():
        scenario.skip('iOS scenario')
        return

    bdd_common_before_scenario(context, scenario)


def bdd_common_before_scenario(context_or_world, scenario):
    """Common scenario initialization in behave or lettuce

    :param context_or_world: behave context or lettuce world
    :param scenario: running scenario
    """
    # Initialize and connect driver wrapper
    create_and_configure_wrapper(context_or_world)
    connect_wrapper(context_or_world)

    # Add assert screenshot methods with scenario configuration
    add_assert_screenshot_methods(context_or_world, scenario)

    # Configure Jira properties
    save_jira_conf()

    # Add implicitly wait
    implicitly_wait = context_or_world.toolium_config.get_optional('Driver', 'implicitly_wait')
    if context_or_world.driver and implicitly_wait:
        context_or_world.driver.implicitly_wait(implicitly_wait)

    context_or_world.logger.info("Running new scenario: {0}".format(scenario.name))


def create_and_configure_wrapper(context_or_world):
    """Create and configure driver wrapper in behave or lettuce tests

    :param context_or_world: behave context or lettuce world
    """
    # Create default driver wrapper
    context_or_world.driver_wrapper = DriverWrappersPool.get_default_wrapper()
    context_or_world.utils = context_or_world.driver_wrapper.utils

    # Get behave userdata properties to override config properties
    try:
        behave_properties = context_or_world.config.userdata
    except AttributeError:
        behave_properties = None

    # Configure wrapper
    context_or_world.driver_wrapper.configure(True, context_or_world.config_files, behave_properties)

    # Copy config object
    context_or_world.toolium_config = context_or_world.driver_wrapper.config

    # Configure logger
    context_or_world.logger = logging.getLogger(__name__)


def connect_wrapper(context_or_world):
    """Connect driver in behave or lettuce tests

    :param context_or_world: behave context or lettuce world
    """
    # Create driver if it is not already created
    if context_or_world.driver_wrapper.driver:
        context_or_world.driver = context_or_world.driver_wrapper.driver
    else:
        context_or_world.driver = context_or_world.driver_wrapper.connect()

    # Copy app_strings object
    context_or_world.app_strings = context_or_world.driver_wrapper.app_strings


def add_assert_screenshot_methods(context_or_world, scenario):
    """Add assert screenshot methods to behave or lettuce object

    :param context_or_world: behave context or lettuce world
    :param scenario: running scenario
    """

    def assert_screenshot(element_or_selector, filename, threshold=0, exclude_elements=[], driver_wrapper=None,
                          force=False):
        file_suffix = scenario.name.replace(' ', '_')
        VisualTest(driver_wrapper, force).assert_screenshot(element_or_selector, filename, file_suffix, threshold,
                                                            exclude_elements)

    def assert_full_screenshot(filename, threshold=0, exclude_elements=[], driver_wrapper=None, force=False):
        file_suffix = scenario.name.replace(' ', '_')
        VisualTest(driver_wrapper, force).assert_screenshot(None, filename, file_suffix, threshold, exclude_elements)

    context_or_world.assert_screenshot = assert_screenshot
    context_or_world.assert_full_screenshot = assert_full_screenshot


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
        context_or_world.logger.error(test_comment)
        # Capture screenshot on error
        DriverWrappersPool.capture_screenshots(scenario_file_name)

    # Save webdriver logs on error or if it is enabled
    test_passed = status == 'passed'
    DriverWrappersPool.save_all_webdriver_logs(scenario.name, test_passed)

    # Close browser and stop driver if it must not be reused
    reuse_driver = context_or_world.toolium_config.getboolean_optional('Driver', 'reuse_driver')
    DriverWrappersPool.close_drivers_and_download_videos(scenario_file_name, test_passed, reuse_driver)

    # Save test status to be updated later
    context_or_world.global_status['test_passed'] = context_or_world.global_status[
                                                        'test_passed'] and test_passed if reuse_driver else test_passed
    add_jira_status(get_jira_key_from_scenario(scenario), test_status, test_comment)


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


def after_all(context):
    """Clean method that will be executed after all features are finished

    :param context: behave context
    """
    bdd_common_after_all(context)


def bdd_common_after_all(context_or_world):
    """Common after all method in behave or lettuce

    :param context_or_world: behave context or lettuce world
    """
    # Close browser and stop driver if it has been reused
    DriverWrappersPool.close_drivers_and_download_videos('multiple_tests',
                                                         context_or_world.global_status['test_passed'])

    # Update tests status in Jira
    change_all_jira_status()
