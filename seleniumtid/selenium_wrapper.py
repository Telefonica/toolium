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
    conf_properties_files = None
    conf_logging_file = None
    browser_info = None
    screenshots_path = None
    screenshots_number = None
    videos_path = None
    videos_number = None
    output_directory = None
    baseline_directory = None
    visual_number = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            # Create new instance
            cls._instance = super(SeleniumWrapper, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def configure_logger(self):
        '''
        Configure selenium instance logger
        '''
        # Get logging filename from system properties
        try:
            conf_logging_file = os.environ["Files_logging"]
        except KeyError:
            conf_logging_file = 'conf/logging.conf'

        # Configure logger if logging filename has changed
        if self.conf_logging_file != conf_logging_file:
            try:
                logging.config.fileConfig(conf_logging_file, None, False)
            except Exception as exc:
                print "[WARN] Error reading logging config file '{}': {}".format(conf_logging_file, exc)
            self.conf_logging_file = conf_logging_file
            self.logger = logging.getLogger(__name__)

    def configure_properties(self):
        '''
        Configure selenium instance properties
        '''
        # Get properties filename from system properties
        try:
            conf_properties_files = os.environ["Files_properties"]
        except KeyError:
            conf_properties_files = 'conf/properties.cfg'

        # Configure config if properties filename has changed
        if self.conf_properties_files != conf_properties_files:
            # Initialize the config object
            self.config = ExtendedConfigParser()
            self.conf_properties_files = conf_properties_files

            # Configure properties (last files could override properties)
            for conf_properties_file in conf_properties_files.split(';'):
                result = self.config.read(conf_properties_file)
                if len(result) == 0:
                    message = 'Properties config file not found: {}'.format(conf_properties_file)
                    self.logger.error(message)
                    raise Exception(message)
                self.logger.debug('Reading properties from file: {}'.format(conf_properties_file))

            # Override properties with system properties
            self.config.update_from_system_properties()

    def configure(self):
        '''
        Configure initial selenium instance using logging and properties files for Selenium or Appium tests
        '''
        # Configure logger
        self.configure_logger()
        # Initialize the config object
        self.configure_properties()

        # Configure folders if browser has changed
        browser_info = self.config.get('Browser', 'browser').replace('-', '_')
        if self.browser_info != browser_info:
            self.browser_info = browser_info

            # Unique screenshots and videos directories
            date = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
            self.screenshots_path = os.path.join(os.getcwd(), 'dist', 'screenshots', date + '_' + browser_info)
            self.screenshots_number = 1
            self.videos_path = os.path.join(os.getcwd(), 'dist', 'videos', date + '_' + browser_info)
            self.videos_number = 1

            # Unique visualtests directories
            visual_path = os.path.join(os.getcwd(), 'dist', 'visualtests')
            self.output_directory = os.path.join(visual_path, date + '_' + browser_info)
            self.baseline_directory = os.path.join(visual_path, 'baseline', browser_info)
            self.visual_number = 1

    def connect(self):
        """
        Set up the browser driver
        """
        self.configure()
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
        return not self.is_mobile_test() or appium_app in ('chrome', 'chromium', 'browser', 'safari')

    def is_maximizable(self):
        '''
        Returns true if the browser is maximizable
        '''
        browser_name = self.config.get('Browser', 'browser').split('-')[0]
        return not self.is_mobile_test() and browser_name != 'opera'
