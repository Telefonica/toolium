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
from selenium_tid_python import selenium_driver


class Utils(object):
    def __init__(self, driver):
        self.driver = driver
        # Configure logger
        self.logger = logging.getLogger(__name__)

    def capture_screenshot(self, name):
        # Capture screenshot
        filename = '{0:0=2d}_{1}.png'.format(selenium_driver.screenshots_number, name)
        filepath = os.path.join(selenium_driver.screenshots_path, filename)
        if not os.path.exists(selenium_driver.screenshots_path):
            os.makedirs(selenium_driver.screenshots_path)
        if self.driver.get_screenshot_as_file(filepath):
            self.logger.info("Saved screenshot " + filepath)
            selenium_driver.screenshots_number += 1

    def print_all_selenium_logs(self):
        map(self.print_selenium_logs, {'browser', 'client', 'driver', 'performance', 'server'})

    def print_selenium_logs(self, log_type):
        for entry in self.driver.get_log(log_type):
            message = entry['message'].rstrip().encode('utf-8')
            self.logger.debug('{0} - {1}: {2}'.format(log_type.title(), entry['level'], message))
