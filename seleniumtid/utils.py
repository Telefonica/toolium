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
import logging
import os
from seleniumtid import selenium_driver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Utils(object):
    driver = None
    logger = None

    def __init__(self, driver):
        self.driver = driver
        # Configure logger
        self.logger = logging.getLogger(__name__)

    def set_implicit_wait(self):
        '''
        Read timeout from configuration properties and set the implicit wait
        '''
        config = selenium_driver.config
        implicitly_wait = config.get_optional('Common', 'implicitly_wait')
        if (implicitly_wait):
            self.driver.implicitly_wait(implicitly_wait)

    def capture_screenshot(self, name):
        '''
        Capture screenshot and save it in screenshots folder
        '''
        filename = '{0:0=2d}_{1}.png'.format(selenium_driver.screenshots_number, name)
        filepath = os.path.join(selenium_driver.screenshots_path, filename)
        if not os.path.exists(selenium_driver.screenshots_path):
            os.makedirs(selenium_driver.screenshots_path)
        if self.driver.get_screenshot_as_file(filepath):
            self.logger.info("Saved screenshot " + filepath)
            selenium_driver.screenshots_number += 1

    def print_all_selenium_logs(self):
        '''
        Print all selenium logs
        '''
        map(self.print_selenium_logs, {'browser', 'client', 'driver', 'performance', 'server', 'logcat'})

    def print_selenium_logs(self, log_type):
        '''
        Print selenium logs of the specified type (browser, client, driver, performance, sever, logcat)
        '''
        for entry in self.driver.get_log(log_type):
            message = entry['message'].rstrip().encode('utf-8')
            self.logger.debug('{0} - {1}: {2}'.format(log_type.title(), entry['level'], message))

    def wait_until_element_not_visible(self, locator, timeout=10):
        '''
        Search element by locator and wait until it is not visible
        '''
        # Remove implicit wait
        self.driver.implicitly_wait(0)
        # Wait for invisibility
        WebDriverWait(self.driver, timeout).until(EC.invisibility_of_element_located(locator))
        # Restore implicit wait from properties
        self.set_implicit_wait()
