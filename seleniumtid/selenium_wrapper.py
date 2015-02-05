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
    driver = None
    logger = None
    config = ExtendedConfigParser()
    screenshots_path = None
    screenshots_number = None
    videos_path = None
    videos_number = None
    output_directory = None
    baseline_directory = None
    visual_number = None

    def configure(self):
        '''
        Configure initial selenium instance using logging and properties files
        '''
        # Initialize the config object
        self.config = ExtendedConfigParser()

        # Get config filenames from system properties
        self.config.add_section('Files')
        self.config.set('Files', 'logging', 'conf/logging.conf')
        self.config.set('Files', 'properties', 'conf/properties.cfg')
        self.config.update_from_system_properties()
        conf_logging_file = self.config.get('Files', 'logging')
        conf_properties_files = self.config.get('Files', 'properties')

        # Configure logger
        try:
            logging.config.fileConfig(conf_logging_file, None, False)
        except Exception as exc:
            print "[WARN] Error reading logging config file '{}': {}".format(conf_logging_file, exc)
        self.logger = logging.getLogger(__name__)

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

        # Unique screenshots and videos directories
        date = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
        browser_info = self.config.get('Browser', 'browser').replace('-', '_')
        self.screenshots_path = os.path.join(os.getcwd(), 'dist', 'screenshots', date + '_' + browser_info)
        self.screenshots_number = 1
        self.videos_path = os.path.join(os.getcwd(), 'dist', 'videos', date + '_' + browser_info)
        self.videos_number = 1

        # Unique visualtests directories
        if self.config.getboolean_optional('Server', 'visualtests_enabled'):
            visual_path = os.path.join(os.getcwd(), 'dist', 'visualtests')
            self.output_directory = os.path.join(visual_path, date + '_' + browser_info)
            self.baseline_directory = os.path.join(visual_path, 'baseline', browser_info)
            if not os.path.exists(self.baseline_directory):
                os.makedirs(self.baseline_directory)
            if not self.config.getboolean_optional('Server', 'visualtests_save'):
                if not os.path.exists(self.output_directory):
                    os.makedirs(self.output_directory)
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
        return not self.is_mobile_test() or appium_app in ('chrome', 'safari')

    def is_maximizable(self):
        '''
        Returns true if the browser is maximizable
        '''
        browser_name = self.config.get('Browser', 'browser').split('-')[0]
        return not self.is_mobile_test() and browser_name != 'opera'
