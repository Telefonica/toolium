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

from lettuce import world

from toolium.behave.environment import bdd_common_before_scenario, bdd_common_after_scenario, bdd_common_after_all
from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrappersPool


def setup_driver(scenario):
    """Scenario initialization

    :param scenario: running scenario
    """
    if not hasattr(world, 'config_files'):
        world.config_files = ConfigFiles()

    # By default config directory is located in terrain path
    if not world.config_files.config_directory:
        world.config_files.set_config_directory(DriverWrappersPool.get_default_config_directory())

    world.global_status = {'test_passed': True}
    bdd_common_before_scenario(world, scenario)


def teardown_driver(scenario):
    """Clean method that will be executed after each scenario

    :param scenario: running scenario
    """
    status = 'failed' if scenario.failed else 'passed'
    bdd_common_after_scenario(world, scenario, status)


def teardown_driver_all(total):
    """Clean method that will be executed after all features are finished

    :param total: results of executed features
    """
    bdd_common_after_all(world)
