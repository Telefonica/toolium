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

import logging
import os
import re
import collections

from behave.api.async_step import use_or_create_async_context

from toolium.utils import dataset
from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrappersPool
from toolium.jira import add_jira_status, change_all_jira_status, save_jira_conf
from toolium.visual_test import VisualTest
from toolium.pageelements import PageElement
from toolium.behave.env_utils import DynamicEnvironment


def before_all(context):
    """Initialization method that will be executed before the test execution

    :param context: behave context
    """
    # Get 'TOOLIUM_CONFIG_ENVIRONMENT' property from user input (e.g. -D TOOLIUM_CONFIG_ENVIRONMENT=ios)
    env = context.config.userdata.get('TOOLIUM_CONFIG_ENVIRONMENT')
    if env:
        os.environ['TOOLIUM_CONFIG_ENVIRONMENT'] = env

    if not hasattr(context, 'config_files'):
        context.config_files = ConfigFiles()
    context.config_files = DriverWrappersPool.initialize_config_files(context.config_files)

    # By default config directory is located in environment path
    if not context.config_files.config_directory:
        context.config_files.set_config_directory(DriverWrappersPool.get_default_config_directory())

    context.global_status = {'test_passed': True}
    create_and_configure_wrapper(context)

    # Dictionary to store information during the whole test execution
    context.run_storage = dict()
    context.storage = context.run_storage

    # Method in context to store values in context.storage, context.feature_storage or context.run_storage from steps
    context.store_key_in_storage = dataset.store_key_in_storage

    # Behave dynamic environment
    context.dyn_env = DynamicEnvironment(logger=context.logger)

    # Initialize dataset behave variables
    dataset.behave_context = context
    dataset.toolium_config = context.toolium_config


def before_feature(context, feature):
    """Feature initialization

    :param context: behave context
    :param feature: running feature
    """
    context.global_status = {'test_passed': True}

    # Start driver if it should be reused in feature
    context.reuse_driver_from_tags = 'reuse_driver' in feature.tags
    if context.toolium_config.getboolean_optional('Driver', 'reuse_driver') or context.reuse_driver_from_tags:
        no_driver = 'no_driver' in feature.tags
        start_driver(context, no_driver)

    # Dictionary to store information between features
    context.feature_storage = dict()
    context.storage = collections.ChainMap(context.feature_storage, context.run_storage)

    # Behave dynamic environment
    context.dyn_env.get_steps_from_feature_description(feature.description)
    context.dyn_env.execute_before_feature_steps(context)


def before_scenario(context, scenario):
    """Scenario initialization

    :param context: behave context
    :param scenario: running scenario
    """
    # Configure reset properties from behave tags
    if 'no_reset_app' in scenario.tags:
        os.environ['TOOLIUM_APPIUMCAPABILITIES_NORESET'] = 'AppiumCapabilities_noReset=true'
        os.environ['TOOLIUM_APPIUMCAPABILITIES_FULLRESET'] = 'AppiumCapabilities_fullReset=false'
    elif 'reset_app' in scenario.tags:
        os.environ['TOOLIUM_APPIUMCAPABILITIES_NORESET'] = 'AppiumCapabilities_noReset=false'
        os.environ['TOOLIUM_APPIUMCAPABILITIES_FULLRESET'] = 'AppiumCapabilities_fullReset=false'
    elif 'full_reset_app' in scenario.tags:
        os.environ['TOOLIUM_APPIUMCAPABILITIES_NORESET'] = 'AppiumCapabilities_noReset=false'
        os.environ['TOOLIUM_APPIUMCAPABILITIES_FULLRESET'] = 'AppiumCapabilities_fullReset=true'

    # Force to reset driver before each scenario if it has @reset_driver tag
    if 'reset_driver' in scenario.tags:
        DriverWrappersPool.stop_drivers()
        DriverWrappersPool.download_videos('multiple tests', context.global_status['test_passed'])
        DriverWrappersPool.save_all_ggr_logs('multiple tests', context.global_status['test_passed'])
        DriverWrappersPool.remove_drivers()
        context.global_status['test_passed'] = True

    # Skip android_only or ios_only scenarios
    if 'android_only' in scenario.tags and context.driver_wrapper.is_ios_test():
        scenario.skip('Android scenario')
        return
    elif 'ios_only' in scenario.tags and context.driver_wrapper.is_android_test():
        scenario.skip('iOS scenario')
        return

    # Read @no_driver tag
    no_driver = 'no_driver' in scenario.tags or 'no_driver' in scenario.feature.tags

    # Initialize and connect driver wrapper
    start_driver(context, no_driver)

    # Add assert screenshot methods with scenario configuration
    add_assert_screenshot_methods(context, scenario)

    # Configure Jira properties
    save_jira_conf()

    context.logger.info("Running new scenario: %s", scenario.name)

    # Make sure context storage dict is empty in each scenario and merge with the rest of storages
    context.storage = collections.ChainMap(dict(), context.feature_storage, context.run_storage)

    # Behave dynamic environment
    context.dyn_env.execute_before_scenario_steps(context)


def create_and_configure_wrapper(context):
    """Create and configure driver wrapper in behave tests

    :param context: behave context
    """
    # Create default driver wrapper
    context.driver_wrapper = DriverWrappersPool.get_default_wrapper()
    context.utils = context.driver_wrapper.utils

    # Get behave userdata properties to override config properties
    try:
        behave_properties = context.config.userdata
    except AttributeError:
        behave_properties = None

    # Configure wrapper
    context.driver_wrapper.configure(context.config_files, behave_properties=behave_properties)

    # Activate behave async context to execute playwright
    if (context.driver_wrapper.config.get_optional('Driver', 'web_library') == 'playwright'
            and context.driver_wrapper.async_loop is None):
        use_or_create_async_context(context)
        context.driver_wrapper.async_loop = context.async_context.loop

    # Copy config object
    context.toolium_config = context.driver_wrapper.config

    # Configure logger
    context.logger = logging.getLogger(__name__)


def connect_wrapper(context):
    """Connect driver in behave tests

    :param context: behave context
    """
    # Create driver if it is not already created
    if context.driver_wrapper.driver:
        context.driver = context.driver_wrapper.driver
    else:
        context.driver = context.driver_wrapper.connect()

    # Copy app_strings object
    context.app_strings = context.driver_wrapper.app_strings


def add_assert_screenshot_methods(context, scenario):
    """Add assert screenshot methods to behave object

    :param context: behave context
    :param scenario: running scenario
    """
    file_suffix = scenario.name

    def assert_screenshot(element_or_selector, filename, threshold=0, exclude_elements=[], driver_wrapper=None,
                          force=False):
        VisualTest(driver_wrapper, force).assert_screenshot(element_or_selector, filename, file_suffix, threshold,
                                                            exclude_elements)

    def assert_full_screenshot(filename, threshold=0, exclude_elements=[], driver_wrapper=None, force=False):
        VisualTest(driver_wrapper, force).assert_screenshot(None, filename, file_suffix, threshold, exclude_elements)

    # Monkey patching assert_screenshot method in PageElement to use the correct test name
    def assert_screenshot_page_element(self, filename, threshold=0, exclude_elements=[], force=False):
        VisualTest(self.driver_wrapper, force).assert_screenshot(self.web_element, filename, file_suffix, threshold,
                                                                 exclude_elements)

    context.assert_screenshot = assert_screenshot
    context.assert_full_screenshot = assert_full_screenshot
    PageElement.assert_screenshot = assert_screenshot_page_element


def after_scenario(context, scenario):
    """Clean method that will be executed after each scenario

    :param context: behave context
    :param scenario: running scenario
    """
    jira_test_status = None
    jira_test_comment = None
    if scenario.status == 'skipped':
        context.logger.info("The scenario '%s' has been skipped", scenario.name)
    elif scenario.status == 'passed':
        jira_test_status = 'Pass'
        context.logger.info("The scenario '%s' has passed", scenario.name)
    else:
        jira_test_status = 'Fail'
        jira_test_comment = "The scenario '%s' has failed" % scenario.name
        context.logger.error("The scenario '%s' has failed", scenario.name)
        context.global_status['test_passed'] = False

    # Close drivers
    DriverWrappersPool.close_drivers(scope='function', test_name=scenario.name,
                                     test_passed=scenario.status in ['passed', 'skipped'], context=context)

    # Save test status to be updated later
    if jira_test_status:
        add_jira_status(get_jira_key_from_scenario(scenario), jira_test_status, jira_test_comment)


def get_jira_key_from_scenario(scenario):
    """Extract Jira Test Case key from scenario tags.
    Two tag formats are allowed:
    @jira('PROJECT-32')
    @jira=PROJECT-32

    :param scenario: behave scenario
    :returns: Jira test case key
    """
    jira_regex = re.compile(r'jira[=\(\']*([A-Z]+\-[0-9]+)[\'\)]*$')
    for tag in scenario.tags:
        match = jira_regex.search(tag)
        if match:
            return match.group(1)
    return None


def after_feature(context, feature):
    """Clean method that will be executed after each feature

    :param context: behave context
    :param feature: running feature
    """
    try:
        # Behave dynamic environment
        context.dyn_env.execute_after_feature_steps(context)
    finally:
        # Close drivers regardless of an Exception being raised due to failed preconditions
        DriverWrappersPool.close_drivers(scope='module', test_name=feature.name,
                                         test_passed=context.global_status['test_passed'])


def after_all(context):
    """Clean method that will be executed after all features are finished

    :param context: behave context
    """
    # Close drivers
    DriverWrappersPool.close_drivers(scope='session', test_name='multiple_tests',
                                     test_passed=context.global_status['test_passed'])

    # Update tests status in Jira
    change_all_jira_status()


def start_driver(context, no_driver):
    """Start driver with configured values

    :param context: behave context
    :param no_driver: True if this is an api test and driver should not be started
    """
    create_and_configure_wrapper(context)
    if not no_driver:
        connect_wrapper(context)
