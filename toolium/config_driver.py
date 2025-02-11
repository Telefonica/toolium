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
import re

from appium import webdriver as appiumdriver
from appium.options.common.base import AppiumOptions
from configparser import NoSectionError
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.ie.options import Options as IeOptions
from selenium.webdriver.ie.service import Service as IeService
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


def get_error_message_from_traceback(traceback):
    """Extract first line of exception message inside traceback

    :param traceback: exception traceback
    :returns: first line of exception message
    """
    # The second line not tabbed of the traceback is the exception message
    lines = traceback.split('\n')[1:]
    for line in lines:
        match = re.match('\\S+: (.*)', line)
        if match:
            return match.group(1)
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
        View valid capabilities in https://www.selenium.dev/documentation/webdriver/drivers/options/

        :returns: a new remote selenium driver
        """
        # Get version and platform capabilities
        capabilities = self._get_capabilities_from_driver_type()

        # Get server url
        server_url = f"{self.utils.get_server_url()}{self.config.get_optional('Server', 'base_path', '')}"

        driver_name = self.utils.get_driver_name()
        if driver_name in ('android', 'ios', 'iphone'):
            # Get driver options
            options = AppiumOptions()
            self._add_capabilities_from_properties(capabilities, 'AppiumCapabilities')
            self._add_capabilities_from_properties(capabilities, 'Capabilities')
            self._update_dict(options.capabilities, capabilities)

            # Create remote appium driver
            driver = appiumdriver.Remote(command_executor=server_url, options=options)
        else:
            # Get driver options
            if driver_name == 'firefox':
                options = self._get_firefox_options(capabilities)
            elif driver_name == 'chrome':
                options = self._get_chrome_options(capabilities)
            elif driver_name == 'safari':
                options = self._get_safari_options(capabilities)
            elif driver_name == 'iexplore':
                options = self._get_explorer_options(capabilities)
            elif driver_name == 'edge':
                options = self._get_edge_options(capabilities)

            # Create remote web driver
            driver = webdriver.Remote(command_executor=server_url, options=options)

            # Add Firefox extesions to driver
            if driver_name == 'firefox':
                self._add_firefox_extensions(driver)

        return driver

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

            # Create local selenium driver
            driver = driver_setup_method()

        return driver

    def _get_capabilities_from_driver_type(self):
        """Extract browserVersion and platformName from driver type and add them to capabilities

        :returns: capabilities dict
        """
        capabilities = {}
        driver_type = self.config.get('Driver', 'type')
        try:
            capabilities['browserVersion'] = driver_type.split('-')[1]
        except IndexError:
            pass

        try:
            # platforName must be lowercase: https://w3c.github.io/webdriver/#dfn-platform-name
            capabilities['platformName'] = driver_type.split('-')[3].lower()
        except IndexError:
            pass

        return capabilities

    def _add_capabilities_from_properties(self, capabilities, section):
        """Add capabilities from properties file

        :param capabilities: capabilities object
        :param section: properties section
        """
        cap_type = {'Capabilities': 'server', 'AppiumCapabilities': 'Appium server'}
        try:
            for cap, cap_value in dict(self.config.items(section)).items():
                if cap not in ['browserVersion', 'platformVersion']:
                    cap_value = self._convert_property_type(cap_value)
                cap = f'appium:{cap}' if section == 'AppiumCapabilities' else cap
                self.logger.debug("Added %s capability: %s = %s", cap_type[section], cap, cap_value)
                self._update_dict(capabilities, {cap: cap_value}, initial_key=cap)
        except NoSectionError:
            pass

    def _setup_firefox(self):
        """Setup Firefox webdriver

        :returns: a new local Firefox driver
        """
        # Get configured options
        firefox_options = self._get_firefox_options()

        # Add headless option
        if self.config.getboolean_optional('Driver', 'headless'):
            self.logger.debug("Running Firefox in headless mode")
            firefox_options.add_argument('-headless')

        # Add Firefox binary
        firefox_binary = self.config.get_optional('Firefox', 'binary')
        if firefox_binary:
            firefox_options.binary = firefox_binary

        # Open driver
        gecko_driver = self.config.get_optional('Driver', 'gecko_driver_path')
        log_path = os.path.join(DriverWrappersPool.output_directory, 'geckodriver.log')
        if gecko_driver:
            self.logger.debug("Gecko driver path given in properties: %s", gecko_driver)
            service = FirefoxService(executable_path=gecko_driver, log_path=log_path)
        else:
            service = FirefoxService(log_path=log_path)
        driver = webdriver.Firefox(service=service, options=firefox_options)

        # Add Firefox extesions to driver
        self._add_firefox_extensions(driver)

        return driver

    def _get_firefox_options(self, capabilities={}):
        """Get Firefox options with given capabilities and configured

        :param capabilities: capabilities object
        :returns: Firefox options object
        """
        firefox_options = FirefoxOptions()
        self._add_firefox_arguments(firefox_options)
        self._add_firefox_preferences(firefox_options)
        self._add_firefox_profile(firefox_options)
        self._add_capabilities_from_properties(capabilities, 'Capabilities')
        self._update_dict(firefox_options.capabilities, capabilities)
        return firefox_options

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

    def _add_firefox_preferences(self, options):
        """Add Firefox preferences from properties file

        :param options: Firefox options object
        """
        try:
            for pref, pref_value in dict(self.config.items('FirefoxPreferences')).items():
                self.logger.debug("Added Firefox preference: %s = %s", pref, pref_value)
                options.set_preference(pref, self._convert_property_type(pref_value))
        except NoSectionError:
            pass

    def _add_firefox_profile(self, options):
        """Add custom Firefox profile

        :param options: Firefox options object
        """
        profile_path = self.config.get_optional('Firefox', 'profile')
        if profile_path:
            self.logger.debug("Using Firefox profile: %s", profile_path)
            options.set_preference('profile', profile_path)

    def _add_firefox_extensions(self, driver):
        """Add Firefox extensions from properties file

        :param driver: Firefox driver
        """
        try:
            for pref, pref_value in dict(self.config.items('FirefoxExtensions')).items():
                self.logger.debug("Added Firefox extension: %s = %s", pref, pref_value)
                webdriver.Firefox.install_addon(driver, pref_value, temporary=True)
        except NoSectionError:
            pass

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

    def _setup_chrome(self):
        """Setup Chrome webdriver

        :returns: a new local Chrome driver
        """
        chrome_driver = self.config.get_optional('Driver', 'chrome_driver_path', None)
        chrome_options = self._get_chrome_options()
        if chrome_driver:
            self.logger.debug("Chrome driver path given in properties: %s", chrome_driver)
            service = ChromeService(executable_path=chrome_driver)
        else:
            service = ChromeService()
        return webdriver.Chrome(service=service, options=chrome_options)

    def _get_chrome_options(self, capabilities={}):
        """Create and configure a Chrome options object

        :param capabilities: capabilities object
        :returns: Chrome options object
        """
        # Get Chrome binary
        chrome_binary = self.config.get_optional('Chrome', 'binary')

        # Create Chrome options
        options = ChromeOptions()

        if self.config.getboolean_optional('Driver', 'headless'):
            self.logger.debug("Running Chrome in headless mode")
            options.add_argument('--headless=new')

        if chrome_binary is not None:
            options.binary_location = chrome_binary

        # Add Chrome preferences, arguments, extensions and mobile emulation options
        self._add_chrome_options(options, 'prefs')
        self._add_chrome_options(options, 'mobileEmulation')
        self._add_chrome_additional_options(options)
        self._add_chrome_arguments(options)
        self._add_chrome_extensions(options)

        # Add capabilities
        self._add_capabilities_from_properties(capabilities, 'Capabilities')
        self._update_dict(options.capabilities, capabilities)

        return options

    def _add_chrome_options(self, options, option_name):
        """Add Chrome options from properties file

        :param options: Chrome options object
        :param option_name: Chrome option name
        """
        options_conf = {
            'prefs': {'section': 'ChromePreferences', 'message': 'preference'},
            'mobileEmulation': {'section': 'ChromeMobileEmulation', 'message': 'mobile emulation option'}
        }
        option_value = dict()
        try:
            for key, value in dict(self.config.items(options_conf[option_name]['section'])).items():
                self.logger.debug("Added Chrome %s: %s = %s", options_conf[option_name]['message'], key, value)
                option_value[key] = self._convert_property_type(value)
            if len(option_value) > 0:
                options.add_experimental_option(option_name, option_value)
        except NoSectionError:
            pass

    def _add_chrome_additional_options(self, options):
        """Add Chrome additional options from properties file

        :param options: Chrome options object
        """
        chrome_options = self.config.get_optional('Chrome', 'options')
        if chrome_options:
            try:
                for key, value in ast.literal_eval(chrome_options).items():
                    self.logger.debug("Added Chrome additional option: %s = %s", key, value)
                    options.add_experimental_option(key, value)
            except Exception as exc:
                self.logger.warning(f'Chrome options "{chrome_options}" can not be added: {exc}')

    def _add_chrome_arguments(self, options):
        """Add Chrome arguments from properties file

        :param options: Chrome options object
        """
        try:
            for pref, pref_value in dict(self.config.items('ChromeArguments')).items():
                pref_value = '={}'.format(pref_value) if pref_value else ''
                self.logger.debug("Added Chrome argument: %s%s", pref, pref_value)
                options.add_argument('{}{}'.format(pref, self._convert_property_type(pref_value)))
        except NoSectionError:
            pass

    def _add_chrome_extensions(self, options):
        """Add Chrome extensions from properties file

        :param options: Chrome options object
        """
        try:
            for pref, pref_value in dict(self.config.items('ChromeExtensions')).items():
                self.logger.debug("Added Chrome extension: %s = %s", pref, pref_value)
                options.add_extension(pref_value)
        except NoSectionError:
            pass

    def _update_dict(self, initial, update, initial_key=None):
        """ Update a initial dict with another dict values recursively

        :param initial: initial dict to be updated
        :param update: new dict
        :param initial_key: update only one key in initial dicts
        :returns: merged dict
        """
        for key, value in update.items():
            if initial_key is None or key == initial_key:
                initial[key] = self._update_dict(initial.get(key, {}), value) if isinstance(value, dict) else value
        return initial

    def _setup_safari(self):
        """Setup Safari webdriver

        :returns: a new local Safari driver
        """
        safari_driver = self.config.get_optional('Driver', 'safari_driver_path', None)
        if safari_driver:
            self.logger.debug("Safari driver path given in properties: %s", safari_driver)
            service = SafariService(executable_path=safari_driver)
        else:
            service = SafariService()
        safari_options = self._get_safari_options()
        return webdriver.Safari(service=service, options=safari_options)

    def _get_safari_options(self, capabilities={}):
        """Create and configure a safari options object

        :param capabilities: capabilities object
        :returns: safari options object
        """
        options = SafariOptions()
        self._add_capabilities_from_properties(capabilities, 'Capabilities')
        self._update_dict(options.capabilities, capabilities)
        return options

    def _setup_explorer(self):
        """Setup Internet Explorer webdriver

        :returns: a new local Internet Explorer driver
        """
        explorer_driver = self.config.get_optional('Driver', 'explorer_driver_path', None)
        if explorer_driver:
            self.logger.debug("Explorer driver path given in properties: %s", explorer_driver)
            service = IeService(executable_path=explorer_driver)
        else:
            service = IeService()
        explorer_options = self._get_explorer_options()
        return webdriver.Ie(service=service, options=explorer_options)

    def _get_explorer_options(self, capabilities={}):
        """Create and configure an explorer options object

        :param capabilities: capabilities object
        :returns: explorer options object
        """
        options = IeOptions()
        self._add_capabilities_from_properties(capabilities, 'Capabilities')
        # Remove custom capabilities to avoid explorer error when unknown capabilities are configured
        capabilities = {key: value for key, value in capabilities.items() if ':' not in key}
        self._update_dict(options.capabilities, capabilities)
        return options

    def _setup_edge(self):
        """Setup Edge webdriver

        :returns: a new local Edge driver
        """
        edge_driver = self.config.get_optional('Driver', 'edge_driver_path', None)
        if edge_driver:
            self.logger.debug("Edge driver path given in properties: %s", edge_driver)
            service = EdgeService(executable_path=edge_driver)
        else:
            service = EdgeService()
        edge_options = self._get_edge_options()
        return webdriver.Edge(service=service, options=edge_options)

    def _get_edge_options(self, capabilities={}):
        """Create and configure an edge options object

        :param capabilities: capabilities object
        :returns: edge options object
        """
        options = EdgeOptions()
        self._add_capabilities_from_properties(capabilities, 'Capabilities')
        self._update_dict(options.capabilities, capabilities)
        return options

    def _setup_appium(self):
        """Setup Appium webdriver

        :returns: a new remote Appium driver
        """
        self.config.set('Server', 'host', '127.0.0.1')
        self.config.set('Server', 'port', '4723')
        return self._create_remote_driver()
