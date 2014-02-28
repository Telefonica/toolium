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


class Utils(object):
    def __init__(self, driver):
        self.driver = driver
        # Configure logger
        self.logger = logging.getLogger(__name__)

    def print_all_selenium_logs(self):
        map(self.print_selenium_logs, {'browser', 'client', 'driver', 'performance', 'server'})

    def print_selenium_logs(self, log_type):
        for entry in self.driver.get_log(log_type):
            message = entry['message'].rstrip().encode('utf-8')
            self.logger.debug('{0} - {1}: {2}'.format(log_type.title(), entry['level'], message))
