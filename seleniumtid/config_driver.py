# -*- coding: utf-8 -*-

u"""
(c) Copyright 2014 Telefónica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefónica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefónica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
"""

from ConfigParser import NoSectionError
from types import MethodType

from selenium import webdriver
from appium import webdriver as appiumdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webdriver import WebDriver as RemoteDriver


try:
    from needle.driver import NeedleWebDriverMixin
except ImportError:
    pass
import logging


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
    return error_message.split('\n', 1)[0]


class ConfigDriver(object):
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config.deepcopy()
        if (self.config.getboolean_optional('VisualTests', 'enabled')
            and 'NeedleWebDriverMixin' not in globals()):
            raise Exception('The visual tests are enabled in properties.cfg, but needle is not installed')

    def create_driver(self):
        """Create a selenium driver using specified config properties

        :returns: a new selenium driver
        :rtype selenium.webdriver.remote.webdriver.WebDriver
        """
        driver = None
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

        if self.config.getboolean_optional('VisualTests', 'enabled'):
            # Add 'public' methods of NeedleWebDriverMixin to the new driver
            for method_name in vars(NeedleWebDriverMixin):
                if not method_name.startswith('__'):
                    bound_method = MethodType(getattr(NeedleWebDriverMixin, method_name).__func__, driver,
                                              RemoteDriver)
                    setattr(driver, method_name, bound_method)

        return driver

    def _create_remotedriver(self):
        """Create a driver in a remote server
        View valid capabilities in https://code.google.com/p/selenium/wiki/DesiredCapabilities

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

        if browser_name == 'android' or browser_name == 'iphone':
            # Add Appium server capabilities
            for cap, cap_value in dict(self.config.items('AppiumCapabilities')).iteritems():
                self.logger.debug("Added server capability: {0} = {1}".format(cap, cap_value))
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
            for pref, pref_value in dict(self.config.items('FirefoxPreferences')).iteritems():
                self.logger.debug("Added firefox preference: {0} = {1}".format(pref, pref_value))
                profile.set_preference(pref, self._convert_property_type(pref_value))
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
        else:
            try:
                return int(value)
            except ValueError:
                return value

    def _setup_chrome(self):
        """Setup Chrome webdriver

        :returns: a new local Chrome driver
        """
        chromedriver = self.config.get('Browser', 'chromedriver_path')
        self.logger.debug("Chrome driver path given in properties: {0}".format(chromedriver))
        return webdriver.Chrome(chromedriver, chrome_options=self._create_chrome_options())

    def _create_chrome_options(self):
        """Create and configure a chrome options object

        :returns: chrome options object
        """
        # Create Chrome options
        options = webdriver.ChromeOptions()

        # Add Chrome preferences
        prefs = dict()
        try:
            for pref, pref_value in dict(self.config.items('ChromePreferences')).iteritems():
                self.logger.debug("Added chrome preference: {0} = {1}".format(pref, pref_value))
                prefs[pref] = self._convert_property_type(pref_value)
            if len(prefs) > 0:
                options.add_experimental_option("prefs", prefs)
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
        seleniumserver = self.config.get('Browser', 'seleniumserver_path')
        self.logger.debug("Selenium server path given in properties: {0}".format(seleniumserver))
        capabilities = DesiredCapabilities.OPERA
        capabilities['opera.autostart'] = True
        capabilities['opera.arguments'] = '-fullscreen'
        return webdriver.Opera(seleniumserver, desired_capabilities=capabilities)

    def _setup_explorer(self):
        """Setup Internet Explorer webdriver

        :returns: a new local Internet Explorer driver
        """
        explorerdriver = self.config.get('Browser', 'explorerdriver_path')
        self.logger.debug("Explorer driver path given in properties: {0}".format(explorerdriver))
        return webdriver.Ie(explorerdriver)

    def _setup_phantomjs(self):
        """Setup phantomjs webdriver

        :returns: a new local phantomjs driver
        """
        phantomdriver = self.config.get('Browser', 'phantomdriver_path')
        self.logger.debug("Phantom driver path given in properties: {0}".format(phantomdriver))
        return webdriver.PhantomJS(executable_path=phantomdriver)

    def _setup_appium(self):
        """Setup Appium webdriver

        :returns: a new remote Appium driver
        """
        self.config.set('Server', 'host', '127.0.0.1')
        self.config.set('Server', 'port', '4723')
        return self._create_remotedriver()
