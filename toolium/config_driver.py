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

import ast
import logging
import os

from appium import webdriver as appiumdriver
from appium.options.common.base import AppiumOptions
from configparser import NoSectionError
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.options import ArgOptions as RemoteOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.ie.service import Service as IEService
from selenium.webdriver.safari.service import Service as SafariService
from selenium.webdriver.safari.options import Options as SafariOptions
from toolium.driver_wrappers_pool import DriverWrappersPool


def get_error_message_from_exception(exception):
    """Extract first line of exception message

    :param exception: exception object
    :returns: first line of exception message
    """
    try:
        return str(exception).split('\n', 1)[0]
    except Exception:
        return ''


class ConfigDriver(object):
    def __init__(self, config, utils=None):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.utils = utils

    def create_driver(self):
        """Create a selenium driver using specified config properties

        :returns: a new selenium driver
        :rtype: selenium.webdriver.remote.webdriver.WebDriver
        """
        driver_type = self.config.get('Driver', 'type')
        try:
            if self.config.getboolean_optional('Server', 'enabled'):
                self.logger.info("Creating remote driver (type = %s)", driver_type)
                driver = self._create_remote_driver()
            else:
                self.logger.info("Creating local driver (type = %s)", driver_type)
                driver = self._create_local_driver()
        except Exception as exc:
            error_message = get_error_message_from_exception(exc)
            self.logger.error("%s driver can not be launched: %s", driver_type.capitalize(), error_message)
            raise

        return driver

    def _create_remote_driver(self):
        """Create a driver in a remote server
        View valid capabilities in https://github.com/SeleniumHQ/selenium/wiki/DesiredCapabilities

        :returns: a new remote selenium driver
        """
        # Get server url
        server_url = '{}/wd/hub'.format(self.utils.get_server_url())

        # Get driver capabilities
        driver_name = self.utils.get_driver_name()
        capabilities = self._get_capabilities_from_driver_type(driver_name)

        # Add version and platform capabilities
        self._add_capabilities_from_driver_type(capabilities)

        options = RemoteOptions()
        self._update_dict(options.capabilities, capabilities)

        # Add custom driver capabilities
        self._add_capabilities_from_properties(capabilities, 'Capabilities')

        if driver_name == 'firefox':
            options = FirefoxOptions()
            options.profile = self._create_firefox_profile()
            self._update_dict(options.capabilities, capabilities)

        if driver_name == 'chrome':
            options = self._create_chrome_options()
            self._update_dict(options.capabilities, capabilities)

        if driver_name in ('android', 'ios', 'iphone'):
            # Create remote appium driver
            self._add_capabilities_from_properties(capabilities, 'AppiumCapabilities')
            options = AppiumOptions()
            self._update_dict(options.capabilities, capabilities)
            return appiumdriver.Remote(command_executor=server_url, options=options)
        else:
            # Create remote web driver
            return webdriver.Remote(command_executor=server_url, options=options)

    def _create_local_driver(self):
        """Create a driver in local machine

        :returns: a new local selenium driver
        """
        driver_name = self.utils.get_driver_name()

        if driver_name in ('android', 'ios', 'iphone'):
            # Create local appium driver
            driver = self._setup_appium()
        else:
            driver_setup = {
                'firefox': self._setup_firefox,
                'chrome': self._setup_chrome,
                'safari': self._setup_safari,
                'iexplore': self._setup_explorer,
                'edge': self._setup_edge
            }
            try:
                driver_setup_method = driver_setup[driver_name]
            except KeyError:
                raise Exception('Unknown driver {0}'.format(driver_name))

            # Get driver capabilities
            capabilities = self._get_capabilities_from_driver_type(driver_name)
            self._add_capabilities_from_properties(capabilities, 'Capabilities')

            # Create local selenium driver
            driver = driver_setup_method(capabilities)

        return driver

    @staticmethod
    def _get_capabilities_from_driver_type(driver_name):
        """Create initial driver capabilities

        :params driver_name: name of selected driver
        :returns: capabilities dictionary
        """
        if driver_name == 'firefox':
            capabilities = DesiredCapabilities.FIREFOX.copy()
        elif driver_name == 'chrome':
            capabilities = DesiredCapabilities.CHROME.copy()
        elif driver_name == 'safari':
            capabilities = DesiredCapabilities.SAFARI.copy()
        elif driver_name == 'iexplore':
            capabilities = DesiredCapabilities.INTERNETEXPLORER.copy()
        elif driver_name == 'edge':
            capabilities = DesiredCapabilities.EDGE.copy()
        elif driver_name in ('android', 'ios', 'iphone'):
            capabilities = {}
        else:
            raise Exception('Unknown driver {0}'.format(driver_name))
        return capabilities

    def _add_capabilities_from_driver_type(self, capabilities):
        """Extract version and platform from driver type and add them to capabilities

        :param capabilities: capabilities dict
        """
        driver_type = self.config.get('Driver', 'type')
        try:
            capabilities['version'] = driver_type.split('-')[1]
        except IndexError:
            pass

        try:
            platforms_list = {'xp': 'XP',
                              'windows_7': 'VISTA',
                              'windows_8': 'WIN8',
                              'windows_10': 'WIN10',
                              'linux': 'LINUX',
                              'android': 'ANDROID',
                              'mac': 'MAC'}
            capabilities['platform'] = platforms_list.get(driver_type.split('-')[3], driver_type.split('-')[3])
        except IndexError:
            pass

    def _add_capabilities_from_properties(self, capabilities, section):
        """Add capabilities from properties file

        :param capabilities: capabilities object
        :param section: properties section
        """
        cap_type = {'Capabilities': 'server', 'AppiumCapabilities': 'Appium server'}
        try:
            for cap, cap_value in dict(self.config.items(section)).items():
                self.logger.debug("Added %s capability: %s = %s", cap_type[section], cap, cap_value)
                cap_value = cap_value if cap == 'version' else self._convert_property_type(cap_value)
                self._update_dict(capabilities, {cap: cap_value}, initial_key=cap)
        except NoSectionError:
            pass

    def _setup_firefox(self, capabilities):
        """Setup Firefox webdriver

        :param capabilities: capabilities object
        :returns: a new local Firefox driver
        """
        if capabilities.get("marionette"):
            gecko_driver = self.config.get('Driver', 'gecko_driver_path')
            self.logger.debug("Gecko driver path given in properties: %s", gecko_driver)
        else:
            gecko_driver = None

        # Get Firefox binary
        firefox_binary = self.config.get_optional('Firefox', 'binary')

        firefox_options = FirefoxOptions()

        if self.config.getboolean_optional('Driver', 'headless'):
            self.logger.debug("Running Firefox in headless mode")
            firefox_options.add_argument('-headless')

        self._add_firefox_arguments(firefox_options)

        if firefox_binary:
            firefox_options.binary = firefox_binary

        log_path = os.path.join(DriverWrappersPool.output_directory, 'geckodriver.log')

        self._update_dict(firefox_options.capabilities, capabilities)
        firefox_options.profile = self._create_firefox_profile()
        service = FirefoxService(executable_path=gecko_driver, log_path=log_path)
        return webdriver.Firefox(service=service, options=firefox_options)

    def _add_firefox_arguments(self, options):
        """Add Firefox arguments from properties file

        :param options: Firefox options object
        """
        try:
            for pref, pref_value in dict(self.config.items('FirefoxArguments')).items():
                pref_value = '={}'.format(pref_value) if pref_value else ''
                self.logger.debug("Added Firefox argument: %s%s", pref, pref_value)
                options.add_argument('{}{}'.format(pref, self._convert_property_type(pref_value)))
        except NoSectionError:
            pass

    def _create_firefox_profile(self):
        """Create and configure a firefox profile

        :returns: firefox profile
        """
        # Get Firefox profile
        profile_directory = self.config.get_optional('Firefox', 'profile')
        if profile_directory:
            self.logger.debug("Using firefox profile: %s", profile_directory)

        # Create Firefox profile
        profile = webdriver.FirefoxProfile(profile_directory=profile_directory)
        profile.native_events_enabled = True

        # Add Firefox preferences
        try:
            for pref, pref_value in dict(self.config.items('FirefoxPreferences')).items():
                self.logger.debug("Added firefox preference: %s = %s", pref, pref_value)
                profile.set_preference(pref, self._convert_property_type(pref_value))
            profile.update_preferences()
        except NoSectionError:
            pass

        # Add Firefox extensions
        try:
            for pref, pref_value in dict(self.config.items('FirefoxExtensions')).items():
                self.logger.debug("Added firefox extension: %s = %s", pref, pref_value)
                profile.add_extension(pref_value)
        except NoSectionError:
            pass

        return profile

    @staticmethod
    def _convert_property_type(value):
        """Converts the string value in a boolean, integer or string

        :param value: string value
        :returns: boolean, integer or string value
        """
        if value in ('true', 'True'):
            formatted_value = True
        elif value in ('false', 'False'):
            formatted_value = False
        elif ((str(value).startswith('{') and str(value).endswith('}'))
              or (str(value).startswith('[') and str(value).endswith(']'))):
            formatted_value = ast.literal_eval(value)
        else:
            try:
                formatted_value = int(value)
            except ValueError:
                formatted_value = value
        return formatted_value

    def _setup_chrome(self, capabilities):
        """Setup Chrome webdriver

        :param capabilities: capabilities object
        :returns: a new local Chrome driver
        """
        chrome_driver = self.config.get('Driver', 'chrome_driver_path')
        self.logger.debug("Chrome driver path given in properties: %s", chrome_driver)
        chrome_options = self._create_chrome_options()
        self._update_dict(chrome_options.capabilities, capabilities)
        service = ChromeService(executable_path=chrome_driver)
        return webdriver.Chrome(service=service, options=chrome_options)

    def _create_chrome_options(self):
        """Create and configure a chrome options object

        :returns: chrome options object
        """
        # Get Chrome binary
        chrome_binary = self.config.get_optional('Chrome', 'binary')

        # Create Chrome options
        options = webdriver.ChromeOptions()

        if self.config.getboolean_optional('Driver', 'headless'):
            self.logger.debug("Running Chrome in headless mode")
            options.add_argument('--headless')
            if os.name == 'nt':  # Temporarily needed if running on Windows.
                options.add_argument('--disable-gpu')

        if chrome_binary is not None:
            options.binary_location = chrome_binary

        # Add Chrome preferences, arguments, extensions and mobile emulation options
        self._add_chrome_options(options, 'prefs')
        self._add_chrome_options(options, 'mobileEmulation')
        self._add_chrome_arguments(options)
        self._add_chrome_extensions(options)

        return options

    def _add_chrome_options(self, options, option_name):
        """Add Chrome options from properties file

        :param options: chrome options object
        :param option_name: chrome option name
        """
        options_conf = {'prefs': {'section': 'ChromePreferences', 'message': 'preference'},
                        'mobileEmulation': {'section': 'ChromeMobileEmulation', 'message': 'mobile emulation option'}}
        option_value = dict()
        try:
            for key, value in dict(self.config.items(options_conf[option_name]['section'])).items():
                self.logger.debug("Added chrome %s: %s = %s", options_conf[option_name]['message'], key, value)
                option_value[key] = self._convert_property_type(value)
            if len(option_value) > 0:
                options.add_experimental_option(option_name, option_value)
        except NoSectionError:
            pass

    def _add_chrome_arguments(self, options):
        """Add Chrome arguments from properties file

        :param options: chrome options object
        """
        try:
            for pref, pref_value in dict(self.config.items('ChromeArguments')).items():
                pref_value = '={}'.format(pref_value) if pref_value else ''
                self.logger.debug("Added chrome argument: %s%s", pref, pref_value)
                options.add_argument('{}{}'.format(pref, self._convert_property_type(pref_value)))
        except NoSectionError:
            pass

    def _add_chrome_extensions(self, options):
        """Add Chrome extensions from properties file

        :param options: chrome options object
        """
        try:
            for pref, pref_value in dict(self.config.items('ChromeExtensions')).items():
                self.logger.debug("Added chrome extension: %s = %s", pref, pref_value)
                options.add_extension(pref_value)
        except NoSectionError:
            pass

    def _update_dict(self, initial, update, initial_key=None):
        """ Update a initial dict with another dict values recursively

        :param initial: initial dict to be updated
        :param update: new dict
        :param initial_key: update only one key in initial dicts
        :return: merged dict
        """
        for key, value in update.items():
            if initial_key is None or key == initial_key:
                initial[key] = self._update_dict(initial.get(key, {}), value) if isinstance(value, dict) else value
        return initial

    def _setup_safari(self, capabilities):
        """Setup Safari webdriver

        :param capabilities: capabilities object
        :returns: a new local Safari driver
        """
        safari_driver = self.config.get('Driver', 'safari_driver_path')
        self.logger.debug("Safari driver path given in properties: %s", safari_driver)
        service = SafariService(executable_path=safari_driver)
        safari_options = SafariOptions()
        self._update_dict(safari_options.capabilities, capabilities)
        return webdriver.Safari(service=service, options=safari_options)

    def _setup_explorer(self, capabilities):
        """Setup Internet Explorer webdriver

        :param capabilities: capabilities object
        :returns: a new local Internet Explorer driver
        """
        explorer_driver = self.config.get('Driver', 'explorer_driver_path')
        self.logger.debug("Explorer driver path given in properties: %s", explorer_driver)
        service = IEService(executable_path=explorer_driver)
        explorer_options = webdriver.IeOptions()
        self._update_dict(explorer_options.capabilities, capabilities)
        return webdriver.Ie(service=service, options=explorer_options)

    def _setup_edge(self, capabilities):
        """Setup Edge webdriver

        :param capabilities: capabilities object
        :returns: a new local Edge driver
        """
        edge_driver = self.config.get('Driver', 'edge_driver_path')
        self.logger.debug("Edge driver path given in properties: %s", edge_driver)
        service = EdgeService(executable_path=edge_driver)
        edge_options = webdriver.EdgeOptions()
        self._update_dict(edge_options.capabilities, capabilities)
        return webdriver.Edge(service=service, options=edge_options)

    def _setup_appium(self):
        """Setup Appium webdriver

        :returns: a new remote Appium driver
        """
        self.config.set('Server', 'host', '127.0.0.1')
        self.config.set('Server', 'port', '4723')
        return self._create_remote_driver()
