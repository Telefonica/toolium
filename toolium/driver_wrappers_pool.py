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

import inspect
import os

import datetime

from toolium.config_files import ConfigFiles
from toolium.utils.path_utils import get_valid_filename, makedirs_safe
from toolium.selenoid import Selenoid


class DriverWrappersPool(object):
    """Driver wrappers pool

    :type driver_wrappers: list of toolium.driver_wrapper.DriverWrapper
    :type config_directory: str
    :type logger: logging.Logger
    :type output_directory: str
    :type screenshots_directory: str
    :type screenshots_number: str
    :type videos_directory: str
    :type logs_directory: str
    :type videos_number: int
    :type visual_baseline_directory: str
    :type visual_output_directory: str
    :type visual_number: int
    """
    driver_wrappers = []  #: driver wrappers list

    # Configuration and output folders
    config_directory = None  #: folder with configuration files
    output_directory = None  #: folder to save output files

    # Screenshots configuration
    screenshots_directory = None  #: folder to save screenshots
    screenshots_number = None  #: number of screenshots taken until now

    # Videos configuration
    videos_directory = None  #: folder to save videos
    logs_directory = None  #: folder to save logs
    videos_number = None  #: number of visual images taken until now

    # Visual Testing configuration
    visual_baseline_directory = None  #: folder to save visual baseline images
    visual_output_directory = None  #: folder to save visual report and images
    visual_number = None  #: number of videos recorded until now

    @classmethod
    def is_empty(cls):
        """Check if the wrappers pool is empty

        :returns: true if the wrappers pool is empty
        """
        return len(cls.driver_wrappers) == 0

    @classmethod
    def get_default_wrapper(cls):
        """Returns the default (first) driver wrapper

        :returns: default driver wrapper
        :rtype: toolium.driver_wrapper.DriverWrapper
        """
        if cls.is_empty():
            # Create a new driver wrapper if the pool is empty
            from toolium.driver_wrapper import DriverWrapper
            DriverWrapper()
        return cls.driver_wrappers[0]

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
            if not driver_wrapper.driver:
                continue
            from toolium.jira import add_attachment
            try:
                add_attachment(driver_wrapper.utils.capture_screenshot(screenshot_name.format(name, driver_index)))
            except Exception:
                # Capture exceptions to avoid errors in teardown method due to session timeouts
                pass
            driver_index += 1

    @classmethod
    def connect_default_driver_wrapper(cls, config_files=None):
        """Get default driver wrapper, configure it and connect driver

        :param config_files: driver wrapper specific config files
        :returns: default driver wrapper
        :rtype: toolium.driver_wrapper.DriverWrapper
        """
        driver_wrapper = cls.get_default_wrapper()
        if not driver_wrapper.driver:
            config_files = DriverWrappersPool.initialize_config_files(config_files)
            driver_wrapper.configure(config_files)
            driver_wrapper.connect()
        return driver_wrapper

    @classmethod
    def close_drivers(cls, scope, test_name, test_passed=True, context=None):
        """Stop all drivers, capture screenshots, copy webdriver and GGR logs and download saved videos

        :param scope: execution scope (function, module, class or session)
        :param test_name: executed test name
        :param test_passed: True if the test has passed
        :param context: behave context
        """
        if scope == 'function':
            # Capture screenshot on error
            if not test_passed:
                cls.capture_screenshots(test_name)
            # Execute behave dynamic environment
            if context and hasattr(context, 'dyn_env'):
                context.dyn_env.execute_after_scenario_steps(context)
            # Save webdriver logs on error or if it is enabled
            cls.save_all_webdriver_logs(test_name, test_passed)

        # Close browser and stop driver if it must not be reused
        reuse_driver = cls.get_default_wrapper().should_reuse_driver(scope, test_passed, context)
        cls.stop_drivers(reuse_driver)
        cls.download_videos(test_name, test_passed, reuse_driver)
        cls.save_all_ggr_logs(test_name, test_passed)
        cls.remove_drivers(reuse_driver)

    @classmethod
    def stop_drivers(cls, maintain_default=False):
        """Stop all drivers except default if it should be reused

        :param maintain_default: True if the default driver should not be closed
        """
        # Exclude first wrapper if the driver must be reused
        driver_wrappers = cls.driver_wrappers[1:] if maintain_default else cls.driver_wrappers

        for driver_wrapper in driver_wrappers:
            if not driver_wrapper.driver:
                continue
            try:
                driver_wrapper.driver.quit()
            except Exception as e:
                driver_wrapper.logger.warn(
                    "Capture exceptions to avoid errors in teardown method due to session timeouts: \n %s" % e)

    @classmethod
    def download_videos(cls, name, test_passed=True, maintain_default=False):
        """Download saved videos if video is enabled or if test fails

        :param name: destination file name
        :param test_passed: True if the test has passed
        :param maintain_default: True if the default driver should not be closed
        """
        # Exclude first wrapper if the driver must be reused
        driver_wrappers = cls.driver_wrappers[1:] if maintain_default else cls.driver_wrappers
        video_name = '{}_driver{}' if len(driver_wrappers) > 1 else '{}'
        video_name = video_name if test_passed else 'error_{}'.format(video_name)
        driver_index = 1

        for driver_wrapper in driver_wrappers:
            if not driver_wrapper.driver:
                continue
            try:
                # Download video if necessary (error case or enabled video)
                if (not test_passed or driver_wrapper.config.getboolean_optional('Server', 'video_enabled', False)) \
                        and driver_wrapper.remote_node_video_enabled:
                    if driver_wrapper.server_type in ['ggr', 'selenoid']:
                        name = get_valid_filename(video_name.format(name, driver_index))
                        Selenoid(driver_wrapper).download_session_video(name)
                    elif driver_wrapper.server_type == 'grid':
                        # Download video from Grid Extras
                        driver_wrapper.utils.download_remote_video(driver_wrapper.remote_node,
                                                                   driver_wrapper.session_id,
                                                                   video_name.format(name, driver_index))
            except Exception as exc:
                # Capture exceptions to avoid errors in teardown method due to session timeouts
                driver_wrapper.logger.warn('Error downloading videos: %s' % exc)
            driver_index += 1

    @classmethod
    def remove_drivers(cls, maintain_default=False):
        """Clean drivers list except default if it should be reused. Drivers must be closed before.

        :param maintain_default: True if the default driver should not be removed
        """
        cls.driver_wrappers = cls.driver_wrappers[0:1] if maintain_default else []

    @classmethod
    def save_all_webdriver_logs(cls, test_name, test_passed):
        """Get all webdriver logs of each driver and write them to log files

        :param test_name: test that has generated these logs
        :param test_passed: True if the test has passed
        """
        cls.save_all_webdriver_or_ggr_logs(test_name, test_passed, ggr=False)

    @classmethod
    def save_all_ggr_logs(cls, test_name, test_passed):
        """Get all GGR logs of each driver and write them to log files

        :param test_name: test that has generated these logs
        :param test_passed: True if the test has passed
        """
        cls.save_all_webdriver_or_ggr_logs(test_name, test_passed, ggr=True)

    @classmethod
    def save_all_webdriver_or_ggr_logs(cls, test_name, test_passed, ggr=False):
        """Get all webdriver or GGR logs of each driver and write them to log files

        :param test_name: test that has generated these logs
        :param test_passed: True if the test has passed
        :param ggr: True if driver should be ggr or selenoid
        """
        log_name = '{} [driver {}]' if len(cls.driver_wrappers) > 1 else '{}'
        driver_index = 1
        for driver_wrapper in cls.driver_wrappers:
            if driver_wrapper.driver and (driver_wrapper.config.getboolean_optional('Server', 'logs_enabled')
                                          or not test_passed):
                try:
                    log_file_name = get_valid_filename(log_name.format(test_name, driver_index))
                    if ggr and driver_wrapper.server_type in ['ggr', 'selenoid']:
                        Selenoid(driver_wrapper).download_session_log(log_file_name)
                    elif not ggr and driver_wrapper.server_type not in ['ggr', 'selenoid']:
                        driver_wrapper.utils.save_webdriver_logs(log_file_name)
                except Exception as exc:
                    # Capture exceptions to avoid errors in teardown method due to session timeouts
                    driver_wrapper.logger.warn('Error downloading webdriver logs: %s' % exc)
            driver_index += 1

    @staticmethod
    def get_configured_value(system_property_name, specific_value, default_value):
        """Get configured value from system properties, method parameters or default value

        :param system_property_name: system property name
        :param specific_value: test case specific value
        :param default_value: default value
        :returns: configured value
        """
        try:
            return os.environ[system_property_name]
        except KeyError:
            return specific_value if specific_value else default_value

    @classmethod
    def configure_common_directories(cls, tc_config_files):
        """Configure common config and output folders for all tests

        :param tc_config_files: test case specific config files
        """
        if cls.config_directory is None:
            # Get config directory from properties
            config_directory = cls.get_configured_value('Config_directory', tc_config_files.config_directory, 'conf')
            prop_filenames = cls.get_configured_value('Config_prop_filenames',
                                                      tc_config_files.config_properties_filenames, 'properties.cfg')
            cls.config_directory = cls._find_parent_directory(config_directory, prop_filenames.split(';')[0])

            # Get output directory from properties and create it
            cls.output_directory = cls.get_configured_value('Output_directory', tc_config_files.output_directory,
                                                            'output')
            if not os.path.isabs(cls.output_directory):
                # If output directory is relative, we use the same path as config directory
                cls.output_directory = os.path.join(os.path.dirname(cls.config_directory), cls.output_directory)
            makedirs_safe(cls.output_directory)

            # Get visual baseline directory from properties
            default_baseline = os.path.join(cls.output_directory, 'visualtests', 'baseline')
            cls.visual_baseline_directory = cls.get_configured_value('Visual_baseline_directory',
                                                                     tc_config_files.visual_baseline_directory,
                                                                     default_baseline)
            if not os.path.isabs(cls.visual_baseline_directory):
                # If baseline directory is relative, we use the same path as config directory
                cls.visual_baseline_directory = os.path.join(os.path.dirname(cls.config_directory),
                                                             cls.visual_baseline_directory)

    @staticmethod
    def get_default_config_directory():
        """Return default config directory, based in the actual test path

        :returns: default config directory
        """
        test_path = os.path.dirname(os.path.realpath(inspect.getouterframes(inspect.currentframe())[2][1]))
        return os.path.join(test_path, 'conf')

    @staticmethod
    def _find_parent_directory(directory, filename):
        """Find a directory in parent tree with a specific filename

        :param directory: directory name to find
        :param filename: filename to find
        :returns: absolute directory path
        """
        parent_directory = directory
        absolute_directory = '.'
        while absolute_directory != os.path.abspath(parent_directory):
            absolute_directory = os.path.abspath(parent_directory)
            if os.path.isfile(os.path.join(absolute_directory, filename)):
                return absolute_directory
            if os.path.isabs(parent_directory):
                parent_directory = os.path.join(os.path.dirname(parent_directory), '..',
                                                os.path.basename(parent_directory))
            else:
                parent_directory = os.path.join('..', parent_directory)
        return os.path.abspath(directory)

    @classmethod
    def configure_visual_directories(cls, driver_info):
        """Configure screenshots, videos and visual directories

        :param driver_info: driver property value to name folders
        """
        if cls.screenshots_directory is None:
            # Unique screenshots and videos directories
            date = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
            folder_name = '%s_%s' % (date, driver_info) if driver_info else date
            folder_name = get_valid_filename(folder_name)
            cls.screenshots_directory = os.path.join(cls.output_directory, 'screenshots', folder_name)
            cls.screenshots_number = 1
            cls.videos_directory = os.path.join(cls.output_directory, 'videos', folder_name)
            cls.logs_directory = os.path.join(cls.output_directory, 'logs', folder_name)
            cls.videos_number = 1

            # Unique visualtests directories
            cls.visual_output_directory = os.path.join(cls.output_directory, 'visualtests', folder_name)
            cls.visual_number = 1

    @staticmethod
    def initialize_config_files(tc_config_files=None):
        """Initialize config files and update config files names with the environment

        :param tc_config_files: test case specific config files
        :returns: initialized config files object
        """
        # Initialize config files
        if tc_config_files is None:
            tc_config_files = ConfigFiles()

        # Update properties and log file names if an environment is configured
        env = DriverWrappersPool.get_configured_value('Config_environment', None, None)
        if env:
            # Update config properties filenames
            prop_filenames = tc_config_files.config_properties_filenames
            new_prop_filenames_list = prop_filenames.split(';') if prop_filenames else ['properties.cfg']
            base, ext = os.path.splitext(new_prop_filenames_list[0])
            new_prop_filenames_list.append('{}-{}{}'.format(env, base, ext))
            new_prop_filenames_list.append('local-{}-{}{}'.format(env, base, ext))
            tc_config_files.set_config_properties_filenames(*new_prop_filenames_list)

            # Update output log filename
            output_log_filename = tc_config_files.output_log_filename
            base, ext = os.path.splitext(output_log_filename) if output_log_filename else ('toolium', '.log')
            tc_config_files.set_output_log_filename('{}_{}{}'.format(base, env, ext))

        return tc_config_files

    @classmethod
    def _empty_pool(cls):
        cls.driver_wrappers = []
        cls.config_directory = None
        cls.output_directory = None
        cls.screenshots_directory = None
        cls.screenshots_number = None
        cls.videos_directory = None
        cls.logs_directory = None
        cls.videos_number = None
        cls.visual_output_directory = None
        cls.visual_number = None
