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
    """Wrapper with the webdriver and the configuration needed to execute tests

    :type driver: selenium.webdriver.remote.webdriver.WebDriver or appium.webdriver.webdriver.WebDriver
    :type config: toolium.config_parser.ExtendedConfigParser or configparser.ConfigParser
    :type utils: toolium.utils.Utils
    :type app_strings: dict
    :type session_id: str
    :type remote_node: str
    :type remote_node_video_enabled: bool
    :type logger: logging.Logger
    :type config_properties_filenames: str
    :type config_log_filename: str
    :type output_log_filename: str
    :type visual_baseline_directory: str
    :type baseline_name: str
    """
    driver = None  #: webdriver instance
    config = ExtendedConfigParser()  #: driver configuration
    utils = None  #: test utils instance
    app_strings = None  #: mobile application strings
    session_id = None  #: remote webdriver session id
    remote_node = None  #: remote grid node
    remote_node_video_enabled = False  #: True if the remote grid node has the video recorder enabled
    logger = None  #: logger instance

    # Configuration and output files
    config_properties_filenames = None  #: configuration filenames separated by commas
    config_log_filename = None  #: configuration log file
    output_log_filename = None  #: output log file
    visual_baseline_directory = None  #: folder with the baseline images
    baseline_name = None  #: baseline name

    def __init__(self):
        if not DriverWrappersPool.is_empty():
            # Copy config object and other properties from default driver
            default_wrapper = DriverWrappersPool.get_default_wrapper()
            self.config = default_wrapper.config.deepcopy()
            self.logger = default_wrapper.logger
            self.config_properties_filenames = default_wrapper.config_properties_filenames
            self.config_log_filename = default_wrapper.config_log_filename
            self.output_log_filename = default_wrapper.output_log_filename
            self.visual_baseline_directory = default_wrapper.visual_baseline_directory
            self.baseline_name = default_wrapper.baseline_name

        # Create utils instance and add wrapper to the pool
        self.utils = Utils(self)
        DriverWrappersPool.add_wrapper(self)

    def configure_logger(self, tc_config_log_filename=None, tc_output_log_filename=None):
        """Configure selenium instance logger

        :param tc_config_log_filename: test case specific logging config file
        :param tc_output_log_filename: test case specific output logger file
        """
        # Get config logger filename
        config_log_filename = DriverWrappersPool.get_configured_value('Config_log_filename', tc_config_log_filename,
                                                                      'logging.conf')
        config_log_filename = os.path.join(DriverWrappersPool.config_directory, config_log_filename)

        # Configure logger only if logging filename has changed
        if self.config_log_filename != config_log_filename:
            # Get output logger filename
            output_log_filename = DriverWrappersPool.get_configured_value('Output_log_filename', tc_output_log_filename,
                                                                          'toolium.log')
            output_log_filename = os.path.join(DriverWrappersPool.output_directory, output_log_filename)
            output_log_filename = output_log_filename.replace('\\', '\\\\')

            try:
                logging.config.fileConfig(config_log_filename, {'logfilename': output_log_filename}, False)
            except Exception as exc:
                print("[WARN] Error reading logging config file '{}': {}".format(config_log_filename, exc))
            self.config_log_filename = config_log_filename
            self.output_log_filename = output_log_filename
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

        # Configure config only if properties filename has changed
        if self.config_properties_filenames != prop_filenames:
            # Initialize the config object
            self.config = ExtendedConfigParser.get_config_from_file(prop_filenames)
            self.config_properties_filenames = prop_filenames

        # Override properties with system properties
        self.config.update_from_system_properties()

    def configure_visual_baseline(self):
        """Configure baseline directory"""
        # Get baseline name
        baseline_name = self.config.get_optional('VisualTests', 'baseline_name', '{Driver_type}')
        for section in self.config.sections():
            for option in self.config.options(section):
                option_value = self.config.get(section, option).replace('-', '_').replace(' ', '_')
                baseline_name = baseline_name.replace('{{{0}_{1}}}'.format(section, option), option_value)

        # Configure baseline directory if baseline name has changed
        if self.baseline_name != baseline_name:
            self.baseline_name = baseline_name
            self.visual_baseline_directory = os.path.join(DriverWrappersPool.output_directory, 'visualtests',
                                                          'baseline', baseline_name)

    def update_visual_baseline(self):
        """Configure baseline directory after driver is created"""
        # Update baseline with real platformVersion value
        if '{PlatformVersion}' in self.baseline_name:
            platform_version = self.driver.desired_capabilities['platformVersion']
            self.baseline_name = self.baseline_name.replace('{PlatformVersion}', str(platform_version))
            self.visual_baseline_directory = os.path.join(DriverWrappersPool.output_directory, 'visualtests',
                                                          'baseline', self.baseline_name)

        # Update baseline with remote node value
        if '{RemoteNode}' in self.baseline_name:
            self.baseline_name = self.baseline_name.replace('{RemoteNode}', str(self.remote_node))
            self.visual_baseline_directory = os.path.join(DriverWrappersPool.output_directory, 'visualtests',
                                                          'baseline', self.baseline_name)

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
            driver_info = self.config.get('Driver', 'type').replace('-', '_')
            DriverWrappersPool.configure_visual_directories(driver_info)
            self.configure_visual_baseline()

    def connect(self, maximize=True):
        """Set up the selenium driver and connect to the server

        :param maximize: True if the driver should be maximized
        :returns: selenium driver
        """
        if not self.config.get('Driver', 'type'):
            return None

        self.driver = ConfigDriver(self.config).create_driver()

        # Save session id and remote node to download video after the test execution
        self.session_id = self.driver.session_id
        self.remote_node = self.utils.get_remote_node()
        self.remote_node_video_enabled = self.utils.is_remote_video_enabled(self.remote_node)

        # Save app_strings in mobile tests
        if self.is_mobile_test() and not self.is_web_test() and self.config.getboolean_optional('Driver',
                                                                                                'appium_app_strings'):
            self.app_strings = self.driver.app_strings()

        # Maximize browser
        if maximize and self.is_maximizable():
            # Set window size or maximize
            window_width = self.config.get_optional('Driver', 'window_width')
            window_height = self.config.get_optional('Driver', 'window_height')
            if window_width and window_height:
                self.driver.set_window_size(window_width, window_height)
            else:
                self.driver.maximize_window()

        # Log window size
        window_size = self.utils.get_window_size()
        self.logger.debug('Window size: {} x {}'.format(window_size['width'], window_size['height']))

        # Update baseline
        self.update_visual_baseline()

        return self.driver

    def is_android_test(self):
        """Check if actual test must be executed in an Android mobile

        :returns: true if test must be executed in an Android mobile
        """
        driver_name = self.config.get('Driver', 'type').split('-')[0]
        return driver_name == 'android'

    def is_ios_test(self):
        """Check if actual test must be executed in an iOS mobile

        :returns: true if test must be executed in an iOS mobile
        """
        driver_name = self.config.get('Driver', 'type').split('-')[0]
        return driver_name in ('ios', 'iphone')

    def is_mobile_test(self):
        """Check if actual test must be executed in a mobile

        :returns: true if test must be executed in a mobile
        """
        return self.is_android_test() or self.is_ios_test()

    def is_web_test(self):
        """Check if actual test must be executed in a browser

        :returns: true if test must be executed in a browser
        """
        appium_browser_name = self.config.get_optional('AppiumCapabilities', 'browserName')
        return not self.is_mobile_test() or appium_browser_name not in (None, '')

    def is_android_web_test(self):
        """Check if actual test must be executed in a browser of an Android mobile

        :returns: true if test must be executed in a browser of an Android mobile
        """
        return self.is_android_test() and self.is_web_test()

    def is_ios_web_test(self):
        """Check if actual test must be executed in a browser of an iOS mobile

        :returns: true if test must be executed in a browser of an iOS mobile
        """
        return self.is_ios_test() and self.is_web_test()

    def is_maximizable(self):
        """Check if the browser is maximizable

        :returns: true if the browser is maximizable
        """
        return not self.is_mobile_test()
