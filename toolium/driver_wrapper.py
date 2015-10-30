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

import logging.config
import os
import datetime

from toolium.config_driver import ConfigDriver
from toolium.config_parser import ExtendedConfigParser


class DriverWrapper(object):
    # Singleton instance
    _instance = None
    driver = None
    logger = None
    config = ExtendedConfigParser()
    browser_info = None
    # Configuration and output files
    config_directory = None
    output_directory = None
    config_properties_filenames = None
    config_log_filename = None
    # Screenshots configuration
    screenshots_directory = None
    screenshots_number = None
    # Videos configuration
    videos_directory = None
    videos_number = None
    # Visual Testing configuration
    visual_output_directory = None
    visual_baseline_directory = None
    visual_number = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            # Create new instance
            cls._instance = super(DriverWrapper, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def get_configured_value(self, system_property_name, specific_value, default_value):
        """Get configured value from system properties, method parameters or default value

        :returns: configured value
        """
        try:
            return os.environ[system_property_name]
        except KeyError:
            return specific_value if specific_value else default_value

    def configure_logger(self, tc_config_log_filename=None, tc_output_log_filename=None):
        """Configure selenium instance logger

        :param tc_config_log_filename: test case specific logging config file
        :param tc_output_log_filename: test case specific output logger file
        """
        # Get config and output logger files
        config_log_filename = self.get_configured_value('Config_log_filename', tc_config_log_filename, 'logging.conf')
        config_log_filename = os.path.join(self.config_directory, config_log_filename)
        output_log_filename = self.get_configured_value('Output_log_filename', tc_output_log_filename, 'toolium.log')
        output_log_filename = os.path.join(self.output_directory, output_log_filename)
        output_log_filename = output_log_filename.replace('\\', '\\\\')

        # Configure logger if logging filename has changed
        if self.config_log_filename != config_log_filename:
            try:
                logging.config.fileConfig(config_log_filename, {'logfilename': output_log_filename}, False)
            except Exception as exc:
                print "[WARN] Error reading logging config file '{}': {}".format(config_log_filename, exc)
            self.config_log_filename = config_log_filename
            self.logger = logging.getLogger(__name__)

    def configure_properties(self, tc_config_prop_filenames=None):
        """Configure selenium instance properties

        :param tc_config_prop_filenames: test case specific properties filenames
        """
        prop_filenames = self.get_configured_value('Config_prop_filenames', tc_config_prop_filenames, 'properties.cfg')
        prop_filenames = [os.path.join(self.config_directory, filename) for filename in prop_filenames.split(';')]
        prop_filenames = ';'.join(prop_filenames)

        # Configure config if properties filename has changed
        if self.config_properties_filenames != prop_filenames:
            # Initialize the config object
            self.config = ExtendedConfigParser.get_config_from_file(prop_filenames)
            self.config_properties_filenames = prop_filenames

            # Override properties with system properties
            self.config.update_from_system_properties()

    def configure_visual_directories(self):
        """Configure screenshots, videos and visual directories"""
        browser_info = self.config.get('Browser', 'browser').replace('-', '_')

        # Configure directories if browser has changed
        if self.browser_info != browser_info:
            self.browser_info = browser_info

            # Unique screenshots and videos directories
            date = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
            self.screenshots_directory = os.path.join(self.output_directory, 'screenshots', date + '_' + browser_info)
            self.screenshots_number = 1
            self.videos_directory = os.path.join(self.output_directory, 'videos', date + '_' + browser_info)
            self.videos_number = 1

            # Unique visualtests directories
            self.visual_output_directory = os.path.join(self.output_directory, 'visualtests', date + '_' + browser_info)
            baseline_name = self.config.get_optional('VisualTests', 'baseline_name')
            if baseline_name:
                language = self.config.get_optional('AppiumCapabilities', 'language', '')
                platform_version = self.config.get_optional('AppiumCapabilities', 'platformVersion', '')
                baseline_name = baseline_name.replace('{browser}', browser_info).replace('{language}', language)
                baseline_name = baseline_name.replace('{platformVersion}', platform_version)
            else:
                baseline_name = browser_info
            self.visual_baseline_directory = os.path.join(self.output_directory, 'visualtests', 'baseline',
                                                          baseline_name)
            self.visual_number = 1

    def configure(self, is_selenium_test=True, tc_config_directory=None, tc_output_directory=None,
                  tc_config_prop_filenames=None, tc_config_log_filename=None, tc_output_log_filename=None):
        """Configure initial selenium instance using logging and properties files for Selenium or Appium tests

        :param is_selenium_test: true if test is a selenium or appium test case
        :param tc_config_directory: test case specific config directory
        :param tc_output_directory: test case specific output directory
        :param tc_config_prop_filenames: test case specific properties filenames
        :param tc_config_log_filename: test case specific logging config filename
        :param tc_output_log_filename: test case specific output logger filename
        """
        # Add warning message when old system properties are configured
        deprecated = (('Files_properties', 'Config_directory and Config_prop_filenames'),
                      ('Files_logging', 'Config_directory and Config_log_filename'),
                      ('Files_log_filename', 'Output_directory and Output_log_filename'),
                      ('Files_output_path', 'Output_directory'))
        for prop in deprecated:
            if self.get_configured_value(prop[0], None, None):
                print('[WARN] {} system property is deprecated, use {} instead'.format(prop[0], prop[1]))

        # Get config and output directories
        self.config_directory = self.get_configured_value('Config_directory', tc_config_directory,
                                                          os.path.join(os.getcwd(), 'conf'))
        self.output_directory = self.get_configured_value('Output_directory', tc_output_directory,
                                                          os.path.join(os.getcwd(), 'output'))
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)

        # Configure logger
        self.configure_logger(tc_config_log_filename, tc_output_log_filename)

        # Initialize the config object
        self.configure_properties(tc_config_prop_filenames)

        # Configure visual directories
        if is_selenium_test:
            self.configure_visual_directories()

    def connect(self):
        """Set up the selenium driver and connect to the server

        :returns: selenium driver
        """
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
        return not self.is_mobile_test() and browser_name != 'edge'
