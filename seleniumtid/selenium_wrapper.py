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
from seleniumtid.config import Config
import logging
import os
import datetime
from seleniumtid.config_driver import ConfigDriver


class SeleniumWrapper(object):
    # Singleton instance
    _instance = None
    driver = None
    logger = None
    config = None
    screenshots_path = None
    screenshots_number = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            # Configure logger
            Config().initialize_logger()
            cls.logger = logging.getLogger(__name__)

            # Configure properties
            cls.config = Config().initialize_config()

            # Unique screenshots directory
            date = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
            browser_info = cls.config.get('Browser', 'browser').replace('-', '_')
            cls.screenshots_path = os.path.join(os.getcwd(), 'dist', 'screenshots', date + '_' + browser_info)
            cls.screenshots_number = 1

            # Create new instance
            cls._instance = super(SeleniumWrapper, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def _get_system_properties(self):
        '''
        Update all config properties values with system property values
        '''
        for section in self.config.sections:
            for option in self.config.options(section):
                self._get_system_property(section, option)

    def _get_system_property(self, section, option):
        '''
        Update a config property value with system property value
        '''
        try:
            propertyName = "{0}_{1}".format(section, option)
            self.config.set(section, option, os.environ[propertyName])
        except KeyError:
            pass

    def connect(self):
        """
        Set up the browser driver
        """
        self.driver = ConfigDriver(self.config).create_driver()
        return self.driver

    def is_mobile_test(self):
        '''
        Returns true if the tests must be executed in a mobile
        '''
        browser_name = self.config.get('Browser', 'browser').split('-')[0]
        return browser_name in ('android', 'iphone')

    def is_web_test(self):
        '''
        Returns true if the tests must be executed in a browser
        '''
        appium_app = self.config.get_optional('AppiumCapabilities', 'app')
        return not self.is_mobile_test() or appium_app in ('chrome', 'safari')

    def is_maximizable(self):
        '''
        Returns true if the browser is maximizable
        '''
        browser_name = self.config.get('Browser', 'browser').split('-')[0]
        return not self.is_mobile_test() and browser_name != 'opera'
