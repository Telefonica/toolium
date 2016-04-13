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

import ast
import logging

# Python 2 and 3 compatibility
from six.moves.configparser import NoSectionError

from appium import webdriver as appiumdriver
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

number_appium_capabilities = ['newCommandTimeout', 'deviceReadyTimeout', 'androidDeviceReadyTimeout', 'adbPort',
                              'avdLaunchTimeout', 'avdReadyTimeout', 'autoWebviewTimeout', 'interKeyDelay',
                              'screenshotWaitTimeout', 'webviewConnectRetries']
boolean_appium_capabilities = ['autoLaunch', 'autoWebview', 'noReset', 'fullReset', 'useKeystore', 'dontStopAppOnReset',
                               'unicodeKeyboard', 'resetKeyboard', 'noSign', 'autoLaunch', 'enablePerformanceLogging',
                               'ignoreUnimportantViews', 'disableAndroidWatchers', 'acceptSslCerts',
                               'locationServicesEnabled', 'locationServicesAuthorized', 'autoAcceptAlerts',
                               'autoDismissAlerts', 'nativeInstrumentsLib', 'nativeWebTap', 'safariAllowPopups',
                               'safariIgnoreFraudWarning', 'safariOpenLinksInBackground', 'keepKeyChains', 'showIOSLog']


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
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config.deepcopy()

    def create_driver(self):
        """Create a selenium driver using specified config properties

        :returns: a new selenium driver
        :rtype: selenium.webdriver.remote.webdriver.WebDriver
        """
        driver_type = self.config.get('Driver', 'type')
        try:
            if self.config.getboolean_optional('Server', 'enabled'):
                self.logger.info("Creating remote driver (type = {0})".format(driver_type))
                driver = self._create_remote_driver()
            else:
                self.logger.info("Creating local driver (type = {0})".format(driver_type))
                driver = self._create_local_driver()
        except Exception as exc:
            error_message = get_error_message_from_exception(exc)
            message = "{0} driver can not be launched: {1}".format(driver_type.capitalize(), error_message)
            self.logger.error(message)
            raise

        return driver

    def _create_remote_driver(self):
        """Create a driver in a remote server
        View valid capabilities in https://github.com/SeleniumHQ/selenium/wiki/DesiredCapabilities

        :returns: a new remote selenium driver
        """
        # Get server url
        server_host = self.config.get('Server', 'host')
        server_port = self.config.get('Server', 'port')
        server_url = 'http://{0}:{1}/wd/hub'.format(server_host, server_port)

        # Get driver capabilities
        driver_type = self.config.get('Driver', 'type')
        driver_name = driver_type.split('-')[0]
        capabilities = self._get_capabilities_from_driver_type(driver_name)

        # Add driver version
        try:
            capabilities['version'] = driver_type.split('-')[1]
        except IndexError:
            pass

        # Add platform capability
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

        if driver_name == 'opera':
            capabilities['opera.autostart'] = True
            capabilities['opera.arguments'] = '-fullscreen'
        elif driver_name == 'firefox':
            capabilities['firefox_profile'] = self._create_firefox_profile().encoded
        elif driver_name == 'chrome':
            capabilities['chromeOptions'] = self._create_chrome_options().to_capabilities()["chromeOptions"]

        # Add custom driver capabilities
        self._add_capabilities_from_properties(capabilities)

        if driver_name in ('android', 'ios', 'iphone'):
            # Create remote appium driver
            self._add_appium_capabilities_from_properties(capabilities)
            return appiumdriver.Remote(command_executor=server_url, desired_capabilities=capabilities)
        else:
            # Create remote web driver
            return webdriver.Remote(command_executor=server_url, desired_capabilities=capabilities)

    def _create_local_driver(self):
        """Create a driver in local machine

        :returns: a new local selenium driver
        """
        driver_type = self.config.get('Driver', 'type')
        driver_name = driver_type.split('-')[0]

        if driver_name in ('android', 'ios', 'iphone'):
            # Create local appium driver
            driver = self._setup_appium()
        else:
            driver_setup = {
                'firefox': self._setup_firefox,
                'chrome': self._setup_chrome,
                'safari': self._setup_safari,
                'opera': self._setup_opera,
                'iexplore': self._setup_explorer,
                'edge': self._setup_edge,
                'phantomjs': self._setup_phantomjs
            }
            driver_setup_method = driver_setup.get(driver_name)
            if not driver_setup_method:
                raise Exception('Unknown driver {0}'.format(driver_name))

            # Get driver capabilities
            capabilities = self._get_capabilities_from_driver_type(driver_name)
            self._add_capabilities_from_properties(capabilities)

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
            return DesiredCapabilities.FIREFOX.copy()
        elif driver_name == 'chrome':
            return DesiredCapabilities.CHROME.copy()
        elif driver_name == 'safari':
            return DesiredCapabilities.SAFARI.copy()
        elif driver_name == 'opera':
            return DesiredCapabilities.OPERA.copy()
        elif driver_name == 'iexplore':
            return DesiredCapabilities.INTERNETEXPLORER.copy()
        elif driver_name == 'edge':
            return DesiredCapabilities.EDGE.copy()
        elif driver_name == 'phantomjs':
            return DesiredCapabilities.PHANTOMJS.copy()
        elif driver_name in ('android', 'ios', 'iphone'):
            return {}
        raise Exception('Unknown driver {0}'.format(driver_name))

    def _add_capabilities_from_properties(self, capabilities):
        """Add capabilities from properties file

        :param capabilities: capabilities object
        """
        try:
            for cap, cap_value in dict(self.config.items('Capabilities')).items():
                self.logger.debug("Added server capability: {0} = {1}".format(cap, cap_value))
                if cap == 'proxy':
                    cap_value = ast.literal_eval(cap_value)
                capabilities[cap] = cap_value
        except NoSectionError:
            pass

    def _add_appium_capabilities_from_properties(self, capabilities):
        """Add Appium capabilities from properties file

        :param capabilities: capabilities object
        """
        for cap, cap_value in dict(self.config.items('AppiumCapabilities')).items():
            self.logger.debug("Added Appium server capability: {0} = {1}".format(cap, cap_value))
            if cap in number_appium_capabilities:
                capabilities[cap] = int(cap_value)
            elif cap in boolean_appium_capabilities:
                capabilities[cap] = cap_value == 'true'
            else:
                capabilities[cap] = cap_value

    def _setup_firefox(self, capabilities):
        """Setup Firefox webdriver

        :param capabilities: capabilities object
        :returns: a new local Firefox driver
        """
        return webdriver.Firefox(firefox_profile=self._create_firefox_profile(), capabilities=capabilities)

    def _create_firefox_profile(self):
        """Create and configure a firefox profile

        :returns: firefox profile
        """
        # Get Firefox profile
        try:
            profile_directory = self.config.get('Firefox', 'profile')
            self.logger.debug("Using firefox profile: {0}".format(profile_directory))
        except NoSectionError:
            profile_directory = None

        # Create Firefox profile
        profile = webdriver.FirefoxProfile(profile_directory=profile_directory)
        profile.native_events_enabled = True

        # Add Firefox preferences
        try:
            for pref, pref_value in dict(self.config.items('FirefoxPreferences')).items():
                self.logger.debug("Added firefox preference: {0} = {1}".format(pref, pref_value))
                profile.set_preference(pref, self._convert_property_type(pref_value))
            profile.update_preferences()
        except NoSectionError:
            pass

        # Add Firefox extensions
        try:
            for pref, pref_value in dict(self.config.items('FirefoxExtensions')).items():
                self.logger.debug("Added firefox extension: {0} = {1}".format(pref, pref_value))
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

    def _setup_chrome(self, capabilities):
        """Setup Chrome webdriver

        :param capabilities: capabilities object
        :returns: a new local Chrome driver
        """
        chrome_driver = self.config.get('Driver', 'chrome_driver_path')
        self.logger.debug("Chrome driver path given in properties: {0}".format(chrome_driver))
        return webdriver.Chrome(chrome_driver, chrome_options=self._create_chrome_options(),
                                desired_capabilities=capabilities)

    def _create_chrome_options(self):
        """Create and configure a chrome options object

        :returns: chrome options object
        """
        # Create Chrome options
        options = webdriver.ChromeOptions()

        # Add Chrome preferences, mobile emulation options and chrome arguments
        self._add_chrome_options(options, 'prefs')
        self._add_chrome_options(options, 'mobileEmulation')
        self._add_chrome_arguments(options)

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
                self.logger.debug("Added chrome {}: {} = {}".format(options_conf[option_name]['message'], key, value))
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
                self.logger.debug("Added chrome argument: {0}{1}".format(pref, pref_value))
                options.add_argument('{}{}'.format(pref, self._convert_property_type(pref_value)))
        except NoSectionError:
            pass

    def _setup_safari(self, capabilities):
        """Setup Safari webdriver

        :param capabilities: capabilities object
        :returns: a new local Safari driver
        """
        return webdriver.Safari(desired_capabilities=capabilities)

    def _setup_opera(self, capabilities):
        """Setup Opera webdriver

        :param capabilities: capabilities object
        :returns: a new local Opera driver
        """
        opera_driver = self.config.get('Driver', 'opera_driver_path')
        self.logger.debug("Opera driver path given in properties: {0}".format(opera_driver))
        return webdriver.Opera(executable_path=opera_driver, desired_capabilities=capabilities)

    def _setup_explorer(self, capabilities):
        """Setup Internet Explorer webdriver

        :param capabilities: capabilities object
        :returns: a new local Internet Explorer driver
        """
        explorer_driver = self.config.get('Driver', 'explorer_driver_path')
        self.logger.debug("Explorer driver path given in properties: {0}".format(explorer_driver))
        return webdriver.Ie(explorer_driver, capabilities=capabilities)

    def _setup_edge(self, capabilities):
        """Setup Edge webdriver

        :param capabilities: capabilities object
        :returns: a new local Edge driver
        """
        edge_driver = self.config.get('Driver', 'edge_driver_path')
        self.logger.debug("Edge driver path given in properties: {0}".format(edge_driver))
        return webdriver.Edge(edge_driver, capabilities=capabilities)

    def _setup_phantomjs(self, capabilities):
        """Setup phantomjs webdriver

        :param capabilities: capabilities object
        :returns: a new local phantomjs driver
        """
        phantomjs_driver = self.config.get('Driver', 'phantomjs_driver_path')
        self.logger.debug("Phantom driver path given in properties: {0}".format(phantomjs_driver))
        return webdriver.PhantomJS(executable_path=phantomjs_driver, desired_capabilities=capabilities)

    def _setup_appium(self):
        """Setup Appium webdriver

        :returns: a new remote Appium driver
        """
        self.config.set('Server', 'host', '127.0.0.1')
        self.config.set('Server', 'port', '4723')
        return self._create_remote_driver()
