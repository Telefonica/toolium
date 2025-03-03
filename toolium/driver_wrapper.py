# -*- coding: utf-8 -*-
"""
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

import screeninfo
from playwright.async_api import async_playwright

from toolium.config_driver import ConfigDriver
from toolium.config_driver_playwright import ConfigDriverPlayWright
from toolium.config_parser import ExtendedConfigParser
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.utils.driver_utils import Utils
from toolium.utils.path_utils import get_valid_filename


class DriverWrapper(object):
    """Wrapper with the webdriver and the configuration needed to execute tests

    :type driver: selenium.webdriver.remote.webdriver.WebDriver or appium.webdriver.webdriver.WebDriver
    :type config: toolium.config_parser.ExtendedConfigParser or configparser.ConfigParser
    :type utils: toolium.utils.driver_utils.Utils
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
    server_type = None  #: remote server type
    remote_node = None  #: remote grid node
    remote_node_video_enabled = False  #: True if the remote grid node has the video recorder enabled
    logger = None  #: logger instance
    async_loop = None  #: async loop for playwright tests
    playwright = None  #: playwright instance
    playwright_browser = None  #: playwright browser instance
    playwright_context = None  #: playwright context instance

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
            self.async_loop = default_wrapper.async_loop
            self.playwright = default_wrapper.playwright
            self.playwright_browser = default_wrapper.playwright_browser
            self.playwright_context = default_wrapper.playwright_context
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
        config_log_filename = DriverWrappersPool.get_configured_value('TOOLIUM_CONFIG_LOG_FILENAME',
                                                                      tc_config_log_filename, 'logging.conf')
        config_log_filename = os.path.join(DriverWrappersPool.config_directory, config_log_filename)

        # Configure logger only if logging filename has changed
        if self.config_log_filename != config_log_filename:
            # Get output logger filename
            output_log_filename = DriverWrappersPool.get_configured_value('TOOLIUM_OUTPUT_LOG_FILENAME',
                                                                          tc_output_log_filename, 'toolium.log')
            output_log_filename = os.path.join(DriverWrappersPool.output_directory, output_log_filename)
            output_log_filename = output_log_filename.replace('\\', '\\\\')

            try:
                logging.config.fileConfig(config_log_filename, {'logfilename': output_log_filename}, False)
            except Exception as exc:
                print("[WARN] Error reading logging config file '{}': {}".format(config_log_filename, exc))
            self.config_log_filename = config_log_filename
            self.output_log_filename = output_log_filename
            self.logger = logging.getLogger(__name__)

    def configure_properties(self, tc_config_prop_filenames=None, behave_properties=None):
        """Configure selenium instance properties

        :param tc_config_prop_filenames: test case specific properties filenames
        :param behave_properties: dict with behave user data properties
        """
        prop_filenames = DriverWrappersPool.get_configured_value('TOOLIUM_CONFIG_PROPERTIES_FILENAMES',
                                                                 tc_config_prop_filenames,
                                                                 'properties.cfg;local-properties.cfg')
        prop_filenames = [os.path.join(DriverWrappersPool.config_directory, filename) for filename in
                          prop_filenames.split(';')]
        prop_filenames = ';'.join(prop_filenames)

        # Configure config only if properties filename has changed
        if self.config_properties_filenames != prop_filenames:
            # Initialize the config object
            self.config = ExtendedConfigParser.get_config_from_file(prop_filenames)
            self.config_properties_filenames = prop_filenames

        # Override properties with toolium system properties
        self.config.update_toolium_system_properties(os.environ)

        # Override properties with behave userdata properties
        if behave_properties:
            self.config.update_properties(behave_properties)

        # Modify config properties before driver creation
        self.finalize_properties_configuration()

    def finalize_properties_configuration(self):
        # Override method if config properties (self.config object) need custom modifications before driver creation
        pass

    def configure_visual_baseline(self):
        """Configure baseline directory"""
        # Get baseline name and translate config variables
        baseline_name = self.config.get_optional('VisualTests', 'baseline_name', '{Driver_type}')
        baseline_name = self.config.translate_config_variables(baseline_name)

        # Configure baseline directory if baseline name has changed
        if self.baseline_name != baseline_name:
            self.baseline_name = baseline_name
            self.visual_baseline_directory = os.path.join(DriverWrappersPool.visual_baseline_directory,
                                                          get_valid_filename(baseline_name))

    def update_visual_baseline(self):
        """Configure baseline directory after driver is created"""
        # Update baseline with real platformVersion value
        if '{PlatformVersion}' in self.baseline_name:
            try:
                platform_version = self.driver.capabilities['platformVersion']
            except KeyError:
                platform_version = None
            self.baseline_name = self.baseline_name.replace('{PlatformVersion}', str(platform_version))
            self.visual_baseline_directory = os.path.join(DriverWrappersPool.visual_baseline_directory,
                                                          self.baseline_name)

        # Update baseline with real version value
        if '{Version}' in self.baseline_name:
            try:
                splitted_version = self.driver.capabilities['browserVersion'].split('.')
                version = '.'.join(splitted_version[:2])
            except KeyError:
                version = None
            self.baseline_name = self.baseline_name.replace('{Version}', str(version))
            self.visual_baseline_directory = os.path.join(DriverWrappersPool.visual_baseline_directory,
                                                          self.baseline_name)

        # Update baseline with remote node value
        if '{RemoteNode}' in self.baseline_name:
            self.baseline_name = self.baseline_name.replace('{RemoteNode}', str(self.remote_node))
            self.visual_baseline_directory = os.path.join(DriverWrappersPool.visual_baseline_directory,
                                                          self.baseline_name)

    def configure(self, tc_config_files, is_selenium_test=True, behave_properties=None):
        """Configure initial selenium instance using logging and properties files for Selenium or Appium tests

        :param tc_config_files: test case specific config files
        :param is_selenium_test: true if test is a selenium or appium test case
        :param behave_properties: dict with behave user data properties
        """
        # Configure config and output directories
        DriverWrappersPool.configure_common_directories(tc_config_files)

        # Configure logger
        self.configure_logger(tc_config_files.config_log_filename, tc_config_files.output_log_filename)

        # Initialize the config object
        self.configure_properties(tc_config_files.config_properties_filenames, behave_properties)

        # Configure visual directories
        if is_selenium_test:
            driver_info = self.config.get('Driver', 'type')
            DriverWrappersPool.configure_visual_directories(driver_info)
            self.configure_visual_baseline()

    def connect(self):
        """Set up the driver and connect to the server

        :returns: selenium or playwright driver
        """
        if not self.config.get('Driver', 'type') or self.config.get('Driver', 'type') in ['api', 'no_driver']:
            return None

        if self.async_loop:
            self.connect_playwright()
        else:
            self.connect_selenium()

        return self.driver

    def connect_selenium(self):
        """Set up selenium driver

        :returns: selenium driver
        """
        self.driver = ConfigDriver(self.config, self.utils).create_driver()

        # Save session id and remote node to download video after the test execution
        self.session_id = self.driver.session_id
        self.server_type, self.remote_node = self.utils.get_remote_node()
        self.remote_node_video_enabled = self.utils.is_remote_video_enabled(self.server_type, self.remote_node)

        # Save app_strings in mobile tests
        if (self.is_mobile_test() and not self.is_web_test()
                and self.config.getboolean_optional('Driver', 'appium_app_strings')):
            self.app_strings = self.driver.app_strings()

        # Resize and move browser
        self.resize_window()

        # Log window size
        window_size = self.utils.get_window_size()
        self.logger.debug('Window size: %s x %s', window_size['width'], window_size['height'])

        # Update baseline
        self.update_visual_baseline()

        # Discard previous logcat logs
        self.utils.discard_logcat_logs()

        # Set implicitly wait timeout
        self.utils.set_implicitly_wait()

    def connect_playwright(self):
        """Set up the playwright page
        It is a sync method because it is called from sync behave initialization method

        :returns: playwright page
        """
        async_loop = self.async_loop
        self.playwright = async_loop.run_until_complete(async_playwright().start())

        # In case of using a persistent context this property must be set and
        # a BrowserContext is returned instead of a Browser
        user_data_dir = self.config.get_optional('PlaywrightContextOptions', 'user_data_dir', None)
        config_driver = ConfigDriverPlayWright(self.config, self.utils, self.playwright)
        if user_data_dir:
            self.playwright_context = async_loop.run_until_complete(
                config_driver.create_playwright_persistent_browser_context()
            )
        else:
            self.playwright_browser = async_loop.run_until_complete(
                config_driver.create_playwright_browser()
            )
            self.playwright_context = async_loop.run_until_complete(
                self.playwright_browser.new_context(**config_driver.get_playwright_context_options())
            )
        self.driver = async_loop.run_until_complete(
            self.playwright_context.new_page(**config_driver.get_playwright_page_options())
        )

    async def connect_playwright_new_page(self):
        """Set up and additional playwright driver creating a new page in current browser and context instance
        It is an async method to be called from async steps or page objects

        :returns: playwright driver
        """

        self.driver = await self.playwright_context.new_page(
            **ConfigDriverPlayWright(self.config, self.utils).get_playwright_page_options()
        )
        return self.driver

    def stop(self):
        """Stop selenium or playwright driver"""
        if self.async_loop:
            # Stop playwright driver
            self.async_loop.run_until_complete(self.playwright_context.close())
        else:
            # Stop selenium driver
            self.driver.quit()

    def resize_window(self):
        """Resize and move browser window"""
        if self.is_maximizable():
            # Configure window bounds
            bounds_x, bounds_y = self.get_config_window_bounds()
            self.driver.set_window_position(bounds_x, bounds_y)
            self.logger.debug('Window bounds: %s x %s', bounds_x, bounds_y)

            # Set window size or maximize
            window_width = self.config.get_optional('Driver', 'window_width')
            window_height = self.config.get_optional('Driver', 'window_height')
            if window_width and window_height:
                self.driver.set_window_size(window_width, window_height)
            else:
                self.driver.maximize_window()

    def get_config_window_bounds(self):
        """Reads bounds from config and, if monitor is specified, modify the values to match with the specified monitor

        :return: coords X and Y where set the browser window.
        """
        bounds_x = int(self.config.get_optional('Driver', 'bounds_x') or 0)
        bounds_y = int(self.config.get_optional('Driver', 'bounds_y') or 0)

        monitor_index = int(self.config.get_optional('Driver', 'monitor') or -1)
        if monitor_index > -1:
            try:
                monitor = screeninfo.get_monitors()[monitor_index]
                bounds_x += monitor.x
                bounds_y += monitor.y
            except NotImplementedError:
                self.logger.warning('Current environment doesn\'t support get_monitors')

        return bounds_x, bounds_y

    def is_android_test(self):
        """Check if actual test must be executed in an Android mobile

        :returns: True if test must be executed in an Android mobile
        """
        return self.utils.get_driver_name() == 'android'

    def is_ios_test(self):
        """Check if actual test must be executed in an iOS mobile

        :returns: True if test must be executed in an iOS mobile
        """
        return self.utils.get_driver_name() in ('ios', 'iphone')

    def is_mac_test(self):
        """Check if actual test must be executed in Mac desktop

        :returns: True if test must be executed in Mac desktop
        """
        return 'mac os' in self.get_driver_platform().lower()

    def is_mobile_test(self):
        """Check if actual test must be executed in a mobile

        :returns: True if test must be executed in a mobile
        """
        return self.is_android_test() or self.is_ios_test()

    def is_web_test(self):
        """Check if actual test must be executed in a browser

        :returns: True if test must be executed in a browser
        """
        appium_browser_name = self.config.get_optional('Capabilities', 'browserName')
        return not self.is_mobile_test() or appium_browser_name not in (None, '')

    def is_android_web_test(self):
        """Check if actual test must be executed in a browser of an Android mobile

        :returns: True if test must be executed in a browser of an Android mobile
        """
        return self.is_android_test() and self.is_web_test()

    def is_ios_web_test(self):
        """Check if actual test must be executed in a browser of an iOS mobile

        :returns: True if test must be executed in a browser of an iOS mobile
        """
        return self.is_ios_test() and self.is_web_test()

    def is_maximizable(self):
        """Check if the browser is maximizable

        :returns: True if the browser is maximizable
        """
        return not self.is_mobile_test()

    def should_reuse_driver(self, scope, test_passed, context=None):
        """Check if the driver should be reused

        :param scope: execution scope (function, module, class or session)
        :param test_passed: True if the test has passed
        :param context: behave context
        :returns: True if the driver should be reused
        """
        reuse_driver = self.config.getboolean_optional('Driver', 'reuse_driver')
        reuse_driver_session = self.config.getboolean_optional('Driver', 'reuse_driver_session')
        restart_driver_after_failure = self.config.getboolean_optional('Driver', 'restart_driver_after_failure')
        if context and scope == 'function':
            reuse_driver = reuse_driver or (hasattr(context, 'reuse_driver_from_tags')
                                            and context.reuse_driver_from_tags)
        return (((reuse_driver and scope == 'function') or (reuse_driver_session and scope != 'session'))
                and (test_passed or not restart_driver_after_failure))

    def get_driver_platform(self):
        """
        Get driver platform where tests are running
        :return: platform name
        """
        return self.driver.capabilities['platformName']
