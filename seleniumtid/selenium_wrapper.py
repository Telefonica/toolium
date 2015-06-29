# -*- coding: utf-8 -*-

u"""
(c) Copyright 2014 Telefónica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefónica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefónica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
"""

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
        """Configure selenium instance logger"""
        # Get logging filename from system properties
        try:
            conf_logging_file = os.environ['Files_logging']
        except KeyError:
            conf_logging_file = os.path.join('conf', 'logging.conf')

        # Get logger filename from system properties
        try:
            log_filename = os.path.normpath(os.environ['Files_log_filename']).replace('\\', '\\\\')
        except KeyError:
            log_filename = 'selenium.log'

        # Configure logger if logging filename has changed
        if self.conf_logging_file != conf_logging_file:
            try:
                logging.config.fileConfig(conf_logging_file, {'logfilename': log_filename}, False)
            except Exception as exc:
                print "[WARN] Error reading logging config file '{}': {}".format(conf_logging_file, exc)
            self.conf_logging_file = conf_logging_file
            self.logger = logging.getLogger(__name__)

    def configure_properties(self):
        """Configure selenium instance properties"""
        # Get properties filename from system properties
        try:
            conf_properties_files = os.environ['Files_properties']
        except KeyError:
            conf_properties_files = os.path.join('conf', 'properties.cfg')

        # Configure config if properties filename has changed
        if self.conf_properties_files != conf_properties_files:
            # Initialize the config object
            self.config = ExtendedConfigParser.get_config_from_file(conf_properties_files)
            self.conf_properties_files = conf_properties_files

            # Override properties with system properties
            self.config.update_from_system_properties()

    def configure(self):
        """Configure initial selenium instance using logging and properties files for Selenium or Appium tests"""
        # Configure logger
        self.configure_logger()
        # Initialize the config object
        self.configure_properties()

        # Configure folders if browser has changed
        browser_info = self.config.get('Browser', 'browser').replace('-', '_')
        if self.browser_info != browser_info:
            self.browser_info = browser_info

            # Get output path from system properties
            try:
                output_path = os.environ['Files_output_path']
            except KeyError:
                output_path = os.path.join(os.getcwd(), 'dist')

            # Unique screenshots and videos directories
            date = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
            self.screenshots_path = os.path.join(output_path, 'screenshots', date + '_' + browser_info)
            self.screenshots_number = 1
            self.videos_path = os.path.join(output_path, 'videos', date + '_' + browser_info)
            self.videos_number = 1

            # Unique visualtests directories
            self.output_directory = os.path.join(output_path, 'visualtests', date + '_' + browser_info)
            baseline_name = self.config.get_optional('VisualTests', 'baseline_name')
            if baseline_name:
                language = self.config.get_optional('AppiumCapabilities', 'language', '')
                platform_version = self.config.get_optional('AppiumCapabilities', 'platformVersion', '')
                baseline_name = baseline_name.replace('{browser}', browser_info).replace('{language}', language)
                baseline_name = baseline_name.replace('{platformVersion}', platform_version)
            else:
                baseline_name = browser_info
            self.baseline_directory = os.path.join(output_path, 'visualtests', 'baseline', baseline_name)
            self.visual_number = 1

    def connect(self):
        """Set up the selenium driver and connect to the server

        :returns: selenium driver
        """
        self.configure()
        self.driver = ConfigDriver(self.config).create_driver()
        return self.driver

    def is_mobile_test(self):
        """Check if actual test must be executed in a mobile

        :returns: true if test must be executed in a mobile
        """
        browser_name = self.config.get('Browser', 'browser').split('-')[0]
        return browser_name in ('android', 'iphone')

    def is_ios_test(self):
        """Check if actual test must be executed in a iOS mobile

        :returns: true if test must be executed in an iOS mobile
        """
        browser_name = self.config.get('Browser', 'browser').split('-')[0]
        return browser_name == 'iphone'

    def is_web_test(self):
        """Check if actual test must be executed in a browser

        :returns: true if test must be executed in a browser
        """
        browser_name = self.config.get_optional('AppiumCapabilities', 'browserName')
        return not self.is_mobile_test() or browser_name not in (None, '')

    def is_maximizable(self):
        """Check if the browser is maximizable

        :returns: true if the browser is maximizable
        """
        browser_name = self.config.get('Browser', 'browser').split('-')[0]
        return not self.is_mobile_test() and browser_name != 'opera'
