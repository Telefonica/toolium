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
import logging.config
import os
import datetime
from seleniumtid.config_driver import ConfigDriver
from seleniumtid.config_parser import ExtendedConfigParser


class SeleniumWrapper(object):
    # Singleton instance
    _instance = None
    driver = None
    logger = None
    config = ExtendedConfigParser()
    screenshots_path = None
    screenshots_number = None
    videos_path = None
    videos_number = None
    output_directory = None
    baseline_directory = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            # Configure logger
            conf_logging_file = 'conf/logging.conf'
            try:
                logging.config.fileConfig(conf_logging_file)
            except Exception:
                print '[WARN] Logging config file not found: {}'.format(conf_logging_file)
            cls.logger = logging.getLogger(__name__)

            # Configure properties
            conf_properties_file = 'conf/properties.cfg'
            result = cls.config.read(conf_properties_file)
            if len(result) == 0:
                print '[ERR] Properties config file not found: {}'.format(conf_properties_file)
            else:
                cls.config.update_from_system_properties()

                # Unique screenshots and videos directories
                date = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
                browser_info = cls.config.get('Browser', 'browser').replace('-', '_')
                cls.screenshots_path = os.path.join(os.getcwd(), 'dist', 'screenshots', date + '_' + browser_info)
                cls.screenshots_number = 1
                cls.videos_path = os.path.join(os.getcwd(), 'dist', 'videos', date + '_' + browser_info)
                cls.videos_number = 1

                # Unique visualtests directories
                if cls.config.getboolean_optional('Server', 'visualtests_enabled'):
                    visual_path = os.path.join(os.getcwd(), 'dist', 'visualtests')
                    cls.output_directory = os.path.join(visual_path, date + '_' + browser_info)
                    cls.baseline_directory = os.path.join(visual_path, 'baseline', browser_info)
                    if not os.path.exists(cls.baseline_directory):
                        os.makedirs(cls.baseline_directory)
                    if not cls.config.getboolean_optional('Server', 'visualtests_save'):
                        if not os.path.exists(cls.output_directory):
                            os.makedirs(cls.output_directory)

            # Create new instance
            cls._instance = super(SeleniumWrapper, cls).__new__(cls, *args, **kwargs)
        return cls._instance

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
