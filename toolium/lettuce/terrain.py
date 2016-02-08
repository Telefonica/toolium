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

from lettuce import before, after, world

from toolium.behave.environment import bdd_common_after_scenario, bdd_common_before_scenario
from toolium.driver_wrapper import DriverWrappersPool
from toolium.jira import change_all_jira_status


@before.each_scenario
def setup_driver(scenario):
    """Scenario initialization

    :param scenario: running scenario
    """

    # Configure logger
    world.logger = logging.getLogger()

    # Get default driver wrapper
    world.driver_wrapper = DriverWrappersPool.get_default_wrapper()

    # Create driver
    world.reuse_driver = world.driver_wrapper.config.getboolean_optional('Common', 'reuse_driver')
    if not world.reuse_driver:
        # Configure wrapper
        world.driver_wrapper.configure()

        # Create driver
        world.driver = world.driver_wrapper.connect()
        world.utils = world.driver_wrapper.utils

    # Common initialization
    bdd_common_before_scenario(world, scenario, world.driver_wrapper)


@after.each_scenario
def teardown_driver(scenario):
    """Clean method that will be executed after each scenario

    :param scenario: running scenario
    """
    status = 'failed' if scenario.failed else 'passed'
    bdd_common_after_scenario(world, scenario, status)


@after.all
def teardown_driver_all(total):
    """Clean method that will be executed after all features are finished

    :param total: results of executed features
    """
    if hasattr(world, 'driver') and world.driver:
        DriverWrappersPool.close_drivers_and_download_videos('multiple_tests')
    # Update tests status in Jira
    change_all_jira_status()
