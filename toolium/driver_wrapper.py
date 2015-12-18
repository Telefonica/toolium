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

import datetime
import logging.config
import os

from toolium.config_driver import ConfigDriver
from toolium.config_files import ConfigFiles
from toolium.config_parser import ExtendedConfigParser


class DriverWrapper(object):
    # Singleton instance
    _instance = None
    driver = None
    utils = None
    session_id = None
    remote_video_node = None
    logger = None
    config = ExtendedConfigParser()
    browser_info = None
    baseline_name = None
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
        if 'main_driver' in kwargs and kwargs['main_driver']:
            if cls._instance:
                # Return the singleton instance
                instance = cls._instance
            else:
                # Create new instance and save it in a class property
                instance = super(DriverWrapper, cls).__new__(cls)
                cls._instance = instance
                DriverWrappersPool.add_wrapper(instance)
        else:
            # Create new instance with a copy of the config object
            instance = super(DriverWrapper, cls).__new__(cls)
            instance.config = cls._instance.config.deepcopy()
            DriverWrappersPool.add_wrapper(instance)
        return instance

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
                print("[WARN] Error reading logging config file '{}': {}".format(config_log_filename, exc))
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
            self.visual_number = 1

        # Get baseline name
        baseline_name = self.config.get_optional('VisualTests', 'baseline_name', '{Browser_browser}')
        for section in self.config.sections():
            for option in self.config.options(section):
                option_value = self.config.get(section, option).replace('-', '_').replace(' ', '_')
                baseline_name = baseline_name.replace('{{{0}_{1}}}'.format(section, option), option_value)

        # Configure baseline directory if baseline name has changed
        if self.baseline_name != baseline_name:
            self.baseline_name = baseline_name
            self.visual_baseline_directory = os.path.join(self.output_directory, 'visualtests', 'baseline',
                                                          baseline_name)

    def configure(self, is_selenium_test=True, tc_config_files=ConfigFiles()):
        """Configure initial selenium instance using logging and properties files for Selenium or Appium tests

        :param is_selenium_test: true if test is a selenium or appium test case
        :param tc_config_files: test case specific config files
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
        self.config_directory = self.get_configured_value('Config_directory', tc_config_files.config_directory,
                                                          os.path.join(os.getcwd(), 'conf'))
        self.output_directory = self.get_configured_value('Output_directory', tc_config_files.output_directory,
                                                          os.path.join(os.getcwd(), 'output'))
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)

        # Configure logger
        self.configure_logger(tc_config_files.config_log_filename, tc_config_files.output_log_filename)

        # Initialize the config object
        self.configure_properties(tc_config_files.config_properties_filenames)

        # Configure visual directories
        if is_selenium_test:
            self.configure_visual_directories()

    def connect(self, maximize=True):
        """Set up the selenium driver and connect to the server

        :param maximize: True if the browser should be maximized
        :returns: selenium driver
        """
        from toolium.utils import Utils
        self.driver = ConfigDriver(self.config).create_driver()
        self.utils = Utils(self)

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


class DriverWrappersPool(object):
    driver_wrappers = []

    @classmethod
    def add_wrapper(cls, driver_wrapper):
        """Add a driver wrapper to the wrappers pool

        :param driver_wrapper: driver_wrapper instance
        """
        cls.driver_wrappers.append(driver_wrapper)

    @classmethod
    def capture_screenshots(cls, name):
        """Capture a screenshot in each driver

        :param name: screenshot name suffix
        """
        screenshot_name = '{}_driver{}' if len(cls.driver_wrappers) > 1 else '{}'
        driver_index = 1
        for driver_wrapper in cls.driver_wrappers:
            if driver_wrapper.utils:
                driver_wrapper.utils.capture_screenshot(screenshot_name.format(name, driver_index))
            driver_index += 1

    @classmethod
    def download_videos(cls, name, test_passed=True):
        """Download saved videos if video is enabled or if test fails

        :param name: destination file name
        :param test_passed: True if the test has passed
        """
        video_name = '{}_driver{}' if len(cls.driver_wrappers) > 1 else '{}'
        driver_index = 1
        for driver_wrapper in cls.driver_wrappers:
            if ((driver_wrapper.config.getboolean_optional('Server', 'video_enabled')
                 or not test_passed) and driver_wrapper.remote_video_node):
                video_name = video_name if test_passed else 'error_{}'.format(video_name)
                driver_wrapper.utils.download_remote_video(driver_wrapper.remote_video_node, driver_wrapper.session_id,
                                                           video_name.format(name, driver_index))

    @classmethod
    def close_drivers(cls):
        """Close browser and stop all drivers"""
        for driver_wrapper in cls.driver_wrappers:
            if driver_wrapper.driver:
                driver_wrapper.driver.quit()
        cls.driver_wrappers = []
