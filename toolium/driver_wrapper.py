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

from toolium.config_driver import ConfigDriver
from toolium.config_files import ConfigFiles
from toolium.config_parser import ExtendedConfigParser
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.utils import Utils


class DriverWrapper(object):
    driver = None
    utils = None
    session_id = None
    remote_video_node = None
    logger = None
    config = ExtendedConfigParser()

    # Configuration and output files
    config_properties_filenames = None
    config_log_filename = None
    visual_baseline_directory = None
    baseline_name = None

    def __init__(self, main_driver=False):
        if not main_driver:
            # Copy config object from default driver
            self.config = DriverWrappersPool.get_default_wrapper().config.deepcopy()

        # Create utils instance and add wrapper to the pool
        self.utils = Utils(self)
        DriverWrappersPool.add_wrapper(self)

    def configure_logger(self, tc_config_log_filename=None, tc_output_log_filename=None):
        """Configure selenium instance logger

        :param tc_config_log_filename: test case specific logging config file
        :param tc_output_log_filename: test case specific output logger file
        """
        # Get config and output logger files
        config_log_filename = DriverWrappersPool.get_configured_value('Config_log_filename', tc_config_log_filename,
                                                                      'logging.conf')
        config_log_filename = os.path.join(DriverWrappersPool.config_directory, config_log_filename)
        output_log_filename = DriverWrappersPool.get_configured_value('Output_log_filename', tc_output_log_filename,
                                                                      'toolium.log')
        output_log_filename = os.path.join(DriverWrappersPool.output_directory, output_log_filename)
        output_log_filename = output_log_filename.replace('\\', '\\\\')

        # Configure logger if logging filename has changed
        if self.config_log_filename != config_log_filename:
            try:
                logging.config.fileConfig(config_log_filename, {'logfilename': output_log_filename}, False)
            except Exception as exc:
                print("[WARN] Error reading logging config file '{}': {}".format(config_log_filename, exc))
            self.config_log_filename = config_log_filename
            self.logger = logging.getLogger(__name__)

    def configure_properties(self, tc_config_prop_filenames=None):
        """Configure selenium instance properties

        :param tc_config_prop_filenames: test case specific properties filenames
        """
        prop_filenames = DriverWrappersPool.get_configured_value('Config_prop_filenames', tc_config_prop_filenames,
                                                                 'properties.cfg')
        prop_filenames = [os.path.join(DriverWrappersPool.config_directory, filename) for filename in
                          prop_filenames.split(';')]
        prop_filenames = ';'.join(prop_filenames)

        # Configure config if properties filename has changed
        if self.config_properties_filenames != prop_filenames:
            # Initialize the config object
            self.config = ExtendedConfigParser.get_config_from_file(prop_filenames)
            self.config_properties_filenames = prop_filenames

            # Override properties with system properties
            self.config.update_from_system_properties()

    def configure_visual_baseline(self):
        """Configure baseline directory"""
        # Get baseline name
        baseline_name = self.config.get_optional('VisualTests', 'baseline_name', '{Browser_browser}')
        for section in self.config.sections():
            for option in self.config.options(section):
                option_value = self.config.get(section, option).replace('-', '_').replace(' ', '_')
                baseline_name = baseline_name.replace('{{{0}_{1}}}'.format(section, option), option_value)

        # Configure baseline directory if baseline name has changed
        if self.baseline_name != baseline_name:
            self.baseline_name = baseline_name
            self.visual_baseline_directory = os.path.join(DriverWrappersPool.output_directory, 'visualtests',
                                                          'baseline', baseline_name)

    def configure(self, is_selenium_test=True, tc_config_files=ConfigFiles()):
        """Configure initial selenium instance using logging and properties files for Selenium or Appium tests

        :param is_selenium_test: true if test is a selenium or appium test case
        :param tc_config_files: test case specific config files
        """
        # Configure config and output directories
        DriverWrappersPool.configure_common_directories(tc_config_files)

        # Configure logger
        self.configure_logger(tc_config_files.config_log_filename, tc_config_files.output_log_filename)

        # Initialize the config object
        self.configure_properties(tc_config_files.config_properties_filenames)

        # Configure visual directories
        if is_selenium_test:
            browser_info = self.config.get('Browser', 'browser').replace('-', '_')
            DriverWrappersPool.configure_visual_directories(browser_info)
            self.configure_visual_baseline()

    def connect(self, maximize=True):
        """Set up the selenium driver and connect to the server

        :param maximize: True if the browser should be maximized
        :returns: selenium driver
        """
        self.driver = ConfigDriver(self.config).create_driver()

        # Save session id and remote node to download video after the test execution
        self.session_id = self.driver.session_id
        self.remote_video_node = self.utils.get_remote_video_node()

        # Maximize browser
        if maximize and self.is_maximizable():
            self.driver.maximize_window()

        return self.driver

    def is_mobile_test(self):
        """Check if actual test must be executed in a mobile

        :returns: true if test must be executed in a mobile
        """
        browser_name = self.config.get('Browser', 'browser').split('-')[0]
        return browser_name in ('android', 'ios', 'iphone')

    def is_ios_test(self):
        """Check if actual test must be executed in an iOS mobile

        :returns: true if test must be executed in an iOS mobile
        """
        browser_name = self.config.get('Browser', 'browser').split('-')[0]
        return browser_name in ('ios', 'iphone')

    def is_android_web_test(self):
        """Check if actual test must be executed in a browser of an Android mobile

        :returns: true if test must be executed in a browser of an Android mobile
        """
        browser_name = self.config.get('Browser', 'browser').split('-')[0]
        appium_browser_name = self.config.get_optional('AppiumCapabilities', 'browserName')
        return browser_name == 'android' and appium_browser_name not in (None, '')

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
