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
from lettuce import before, after, world
from seleniumtid import selenium_driver
from seleniumtid.utils import Utils
import logging
import sys


@before.each_scenario
def setup_driver(scenario):
    # Configure logger
    world.logger = logging.getLogger()
    # Create driver
    if not hasattr(world, 'driver') or not world.driver:
        world.driver = selenium_driver.connect()
    # Add implicitly wait
    implicitly_wait = selenium_driver.config.get_optional('Common', 'implicitly_wait')
    if (implicitly_wait):
        world.driver.implicitly_wait(implicitly_wait)
    # Maximize browser
    if selenium_driver.is_maximizable():
        world.driver.maximize_window()


@after.each_scenario
def teardown_driver(scenario):
    # Check test result
    result = sys.exc_info()
    if result != (None, None, None):
        # TODO: the error check is wrong, never enters here
        Utils(world.driver).capture_screenshot(scenario.name.replace(' ', '_'))

    # Close browser and stop driver
    reuse_driver = selenium_driver.config.get_optional('Common', 'reuse_driver')
    if not reuse_driver:
        world.driver.quit()
        world.driver = None


@after.all
def teardown_driver_all(total):
    if hasattr(world, 'driver') and world.driver:
        world.driver.quit()
        world.driver = None
