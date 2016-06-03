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
import inspect
import logging
import os


class DriverWrappersPool(object):
    """Driver wrappers pool

    :type driver_wrappers: list of toolium.driver_wrapper.DriverWrapper
    :type config_directory: str
    :type logger: logging.Logger
    :type output_directory: str
    :type screenshots_directory: str
    :type screenshots_number: str
    :type videos_directory: str
    :type videos_number: int
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
    videos_number = None  #: number of visual images taken until now

    # Visual Testing configuration
    visual_output_directory = None  #: number of videos recorded until now
    visual_number = None  #: folder to save visual report and images

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
            if driver_wrapper.driver:
                from toolium.jira import add_attachment
                try:
                    add_attachment(driver_wrapper.utils.capture_screenshot(screenshot_name.format(name, driver_index)))
                except Exception:
                    # Capture exceptions to avoid errors in teardown method due to session timeouts
                    pass
            driver_index += 1

    @classmethod
    def download_video(cls, driver_wrapper, name, test_passed=True):
        """Download saved videos if video is enabled or if test fails

        :oaram driver_wrapper: driver wrapper instance
        :param name: destination file name
        :param test_passed: True if the test has passed
        """
        video_name = '{}_driver{}' if len(cls.driver_wrappers) > 1 else '{}'
        driver_index = 1
        if (driver_wrapper.config.getboolean_optional('Server', 'video_enabled') or
                not test_passed) and driver_wrapper.remote_node_video_enabled:
            video_name = video_name if test_passed else 'error_{}'.format(video_name)
            driver_wrapper.utils.download_remote_video(driver_wrapper.remote_node, driver_wrapper.session_id,
                                                       video_name.format(name, driver_index))

    @classmethod
    def close_drivers_and_download_videos(cls, name, test_passed=True, maintain_default=False):
        """Stop all drivers and download saved videos if video is enabled or if test fails

        :param name: destination file name
        :param test_passed: True if the test has passed
        :param maintain_default: True if the default driver should not be closed
        """
        # Exclude first wrapper if the driver must be reused
        driver_wrappers = cls.driver_wrappers[1:] if maintain_default else cls.driver_wrappers

        for driver_wrapper in driver_wrappers:
            if driver_wrapper.driver:
                try:
                    driver_wrapper.driver.quit()
                    cls.download_video(driver_wrapper, name, test_passed)
                except Exception:
                    # Capture exceptions to avoid errors in teardown method due to session timeouts
                    pass

        cls.driver_wrappers = cls.driver_wrappers[0:1] if maintain_default else []

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
            if not os.path.exists(cls.output_directory):
                os.makedirs(cls.output_directory)

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

        :param driver_info: driver property value to rename folders
        """
        if cls.screenshots_directory is None:
            # Unique screenshots and videos directories
            date = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
            cls.screenshots_directory = os.path.join(cls.output_directory, 'screenshots', date + '_' + driver_info)
            cls.screenshots_number = 1
            cls.videos_directory = os.path.join(cls.output_directory, 'videos', date + '_' + driver_info)
            cls.videos_number = 1

            # Unique visualtests directories
            cls.visual_output_directory = os.path.join(cls.output_directory, 'visualtests', date + '_' + driver_info)
            cls.visual_number = 1

    @classmethod
    def _empty_pool(cls):
        cls.driver_wrappers = []
        cls.config_directory = None
        cls.output_directory = None
        cls.screenshots_directory = None
        cls.screenshots_number = None
        cls.videos_directory = None
        cls.videos_number = None
        cls.visual_output_directory = None
        cls.visual_number = None
