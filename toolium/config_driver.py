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

try:
    from configparser import NoSectionError
except ImportError:
    from ConfigParser import NoSectionError
import ast
import logging

from selenium import webdriver
from appium import webdriver as appiumdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


def get_error_message_from_exception(exception):
    """Extract first line of exception message

    :param exception: exception object
    :returns: first line of exception message
    """
    try:
        error_message = exception.msg
    except AttributeError:
        # Get error message in ddt tests
        error_message = exception.message
    return error_message.split('\n', 1)[0] if error_message else ''


class ConfigDriver(object):
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config.deepcopy()

    def create_driver(self):
        """Create a selenium driver using specified config properties

        :returns: a new selenium driver
        :rtype: selenium.webdriver.remote.webdriver.WebDriver
        """
        browser = self.config.get('Browser', 'browser')
        try:
            if self.config.getboolean_optional('Server', 'enabled'):
                self.logger.info("Creating remote driver (browser = {0})".format(browser))
                driver = self._create_remotedriver()
            else:
                self.logger.info("Creating local driver (browser = {0})".format(browser))
                driver = self._create_localdriver()
        except Exception as exc:
            error_message = get_error_message_from_exception(exc)
            message = "{0} driver can not be launched: {1}".format(browser.capitalize(), error_message)
            self.logger.error(message)
            raise

        return driver

    def _create_remotedriver(self):
        """Create a driver in a remote server
        View valid capabilities in https://github.com/SeleniumHQ/selenium/wiki/DesiredCapabilities

        :returns: a new remote selenium driver
        """
        # Get server url
        server_host = self.config.get('Server', 'host')
        server_port = self.config.get('Server', 'port')
        server_url = 'http://{0}:{1}/wd/hub'.format(server_host, server_port)

        # Get browser type capabilities
        capabilities_list = {'firefox': DesiredCapabilities.FIREFOX,
                             'chrome': DesiredCapabilities.CHROME,
                             'safari': DesiredCapabilities.SAFARI,
                             'opera': DesiredCapabilities.OPERA,
                             'iexplore': DesiredCapabilities.INTERNETEXPLORER,
                             'edge': DesiredCapabilities.EDGE,
                             'phantomjs': DesiredCapabilities.PHANTOMJS,
                             'android': DesiredCapabilities.ANDROID,
                             'iphone': DesiredCapabilities.IPHONE}
        browser = self.config.get('Browser', 'browser')
        browser_name = browser.split('-')[0]
        capabilities = capabilities_list.get(browser_name)
        if not capabilities:
            raise Exception('Unknown driver {0}'.format(browser_name))

        # Add browser version
        try:
            capabilities['version'] = browser.split('-')[1]
        except IndexError:
            pass

        # Add platform capability
        try:
            platforms_list = {'xp': 'XP',
                              'windows_7': 'VISTA',
                              'windows_8': 'WIN8',
                              'windows_10': 'WINDOWS',
                              'linux': 'LINUX',
                              'android': 'ANDROID',
                              'mac': 'MAC'}
            capabilities['platform'] = platforms_list.get(browser.split('-')[3], browser.split('-')[3])
        except IndexError:
            pass

        if browser_name == 'opera':
            capabilities['opera.autostart'] = True
            capabilities['opera.arguments'] = '-fullscreen'
        elif browser_name == 'firefox':
            capabilities['firefox_profile'] = self._create_firefox_profile().encoded
        elif browser_name == 'chrome':
            capabilities['chromeOptions'] = self._create_chrome_options().to_capabilities()["chromeOptions"]

        # Add custom driver capabilities
        try:
            for cap, cap_value in dict(self.config.items('Capabilities')).items():
                self.logger.debug("Added server capability: {0} = {1}".format(cap, cap_value))
                capabilities[cap] = cap_value
        except NoSectionError:
            pass

        if browser_name == 'android' or browser_name == 'iphone':
            # Add Appium server capabilities
            for cap, cap_value in dict(self.config.items('AppiumCapabilities')).items():
                self.logger.debug("Added Appium server capability: {0} = {1}".format(cap, cap_value))
                capabilities[cap] = cap_value

            # Create remote appium driver
            return appiumdriver.Remote(command_executor=server_url, desired_capabilities=capabilities)
        else:
            # Create remote web driver
            return webdriver.Remote(command_executor=server_url, desired_capabilities=capabilities)

    def _create_localdriver(self):
        """Create a driver in local machine

        :returns: a new local selenium driver
        """
        browser = self.config.get('Browser', 'browser')
        browser_name = browser.split('-')[0]
        browser_config = {'firefox': self._setup_firefox,
                          'chrome': self._setup_chrome,
                          'safari': self._setup_safari,
                          'opera': self._setup_opera,
                          'iexplore': self._setup_explorer,
                          'edge': self._setup_edge,
                          'phantomjs': self._setup_phantomjs,
                          'android': self._setup_appium,
                          'iphone': self._setup_appium}
        setup_driver_method = browser_config.get(browser_name)
        if not setup_driver_method:
            raise Exception('Unknown driver {0}'.format(browser_name))

        return setup_driver_method()

    def _setup_firefox(self):
        """Setup Firefox webdriver

        :returns: a new local Firefox driver
        """
        return webdriver.Firefox(firefox_profile=self._create_firefox_profile())

    def _create_firefox_profile(self):
        """Create and configure a firefox profile

        :returns: firefox profile
        """
        # Create Firefox profile
        profile = webdriver.FirefoxProfile()
        profile.native_events_enabled = True

        # Add Firefox preferences
        try:
            for pref, pref_value in dict(self.config.items('FirefoxPreferences')).items():
                self.logger.debug("Added firefox preference: {0} = {1}".format(pref, pref_value))
                profile.set_preference(pref, self._convert_property_type(pref_value))
            profile.update_preferences()
        except NoSectionError:
            pass

        return profile

    def _convert_property_type(self, value):
        """Converts the string value in a boolean, integer or string

        :param value: string value
        :returns: boolean, integer or string value
        """
        if value in ('true', 'True'):
            return True
        elif value in ('false', 'False'):
            return False
        elif str(value).startswith('{') and str(value).endswith('}'):
            return ast.literal_eval(value)
        else:
            try:
                return int(value)
            except ValueError:
                return value

    def _setup_chrome(self):
        """Setup Chrome webdriver

        :returns: a new local Chrome driver
        """
        chrome_driver = self.config.get('Browser', 'chromedriver_path')
        self.logger.debug("Chrome driver path given in properties: {0}".format(chrome_driver))
        return webdriver.Chrome(chrome_driver, chrome_options=self._create_chrome_options())

    def _create_chrome_options(self):
        """Create and configure a chrome options object

        :returns: chrome options object
        """
        # Create Chrome options
        options = webdriver.ChromeOptions()

        # Add Chrome preferences
        prefs = dict()
        try:
            for pref, pref_value in dict(self.config.items('ChromePreferences')).items():
                self.logger.debug("Added chrome preference: {0} = {1}".format(pref, pref_value))
                prefs[pref] = self._convert_property_type(pref_value)
            if len(prefs) > 0:
                options.add_experimental_option("prefs", prefs)
        except NoSectionError:
            pass

        # Add Chrome mobile emulation options
        prefs = dict()
        try:
            for pref, pref_value in dict(self.config.items('ChromeMobileEmulation')).items():
                self.logger.debug("Added chrome mobile emulation option: {0} = {1}".format(pref, pref_value))
                prefs[pref] = self._convert_property_type(pref_value)
            if len(prefs) > 0:
                options.add_experimental_option("mobileEmulation", prefs)
        except NoSectionError:
            pass

        # Temporal option to solve https://code.google.com/p/chromedriver/issues/detail?id=799
        options.add_argument("test-type")
        return options

    def _setup_safari(self):
        """Setup Safari webdriver

        :returns: a new local Safari driver
        """
        return webdriver.Safari()

    def _setup_opera(self):
        """Setup Opera webdriver

        :returns: a new local Opera driver
        """
        opera_driver = self.config.get('Browser', 'operadriver_path')
        self.logger.debug("Opera driver path given in properties: {0}".format(opera_driver))
        capabilities = DesiredCapabilities.OPERA
        return webdriver.Opera(executable_path=opera_driver, desired_capabilities=capabilities)

    def _setup_explorer(self):
        """Setup Internet Explorer webdriver

        :returns: a new local Internet Explorer driver
        """
        explorer_driver = self.config.get('Browser', 'explorerdriver_path')
        self.logger.debug("Explorer driver path given in properties: {0}".format(explorer_driver))
        return webdriver.Ie(explorer_driver)

    def _setup_edge(self):
        """Setup Edge webdriver

        :returns: a new local Edge driver
        """
        edge_driver = self.config.get('Browser', 'edgedriver_path')
        self.logger.debug("Edge driver path given in properties: {0}".format(edge_driver))
        return webdriver.Edge(edge_driver)

    def _setup_phantomjs(self):
        """Setup phantomjs webdriver

        :returns: a new local phantomjs driver
        """
        phantom_driver = self.config.get('Browser', 'phantomdriver_path')
        self.logger.debug("Phantom driver path given in properties: {0}".format(phantom_driver))
        return webdriver.PhantomJS(executable_path=phantom_driver)

    def _setup_appium(self):
        """Setup Appium webdriver

        :returns: a new remote Appium driver
        """
        self.config.set('Server', 'host', '127.0.0.1')
        self.config.set('Server', 'port', '4723')
        return self._create_remotedriver()
