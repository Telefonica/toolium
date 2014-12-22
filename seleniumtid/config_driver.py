# -*- coding: utf-8 -*-
'''
(c) Copyright 2014 Telefonica, I+D. Printed in Spain (Europe). All Rights
Reserved.

The copyright to the software program(s) is property of Telefonica I+D.
The program(s) may be used and or copied only with the express written
consent of Telefonica I+D or in accordance with the terms and conditions
stipulated in the agreement/contract under which the program(s) have
been supplied.
'''
from selenium import webdriver
from appium import webdriver as appiumdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging
from nose.tools import assert_is_not_none


def get_error_message_from_exception(exception):
    '''
    Extract first line of exception message
    '''
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

    def create_driver(self):
        """
        Create a selenium driver using specified config properties
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

        return driver

    def _create_remotedriver(self):
        """
        Create a driver in a remote server
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
        assert_is_not_none(capabilities, 'Unknown driver {0}'.format(browser_name))

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
                              'mac': 'MAC'}
            capabilities['platform'] = platforms_list.get(browser.split('-')[3])
        except IndexError:
            pass

        if browser_name == 'opera':
            capabilities['opera.autostart'] = True
            capabilities['opera.arguments'] = '-fullscreen'

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
        """
        Create a driver in local machine
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
        assert_is_not_none(setup_driver_method, 'Unknown driver {0}'.format(browser_name))

        return setup_driver_method()

    def _setup_firefox(self):
        """
        Setup Firefox webdriver
        """
        profile = webdriver.FirefoxProfile()
        profile.native_events_enabled = True
        return webdriver.Firefox(firefox_profile=profile)

    def _setup_chrome(self):
        """
        Setup Chrome webdriver
        """
        chromedriver = self.config.get('Browser', 'chromedriver_path')
        self.logger.debug("Chrome driver path given in properties: {0}".format(chromedriver))
        options = webdriver.ChromeOptions()
        # Temporal option to solve https://code.google.com/p/chromedriver/issues/detail?id=799
        options.add_argument("test-type")
        return webdriver.Chrome(chromedriver, chrome_options=options)

    def _setup_safari(self):
        """
        Setup Safari webdriver
        """
        return webdriver.Safari()

    def _setup_opera(self):
        """
        Setup Opera webdriver
        """
        seleniumserver = self.config.get('Browser', 'seleniumserver_path')
        self.logger.debug("Selenium server path given in properties: {0}".format(seleniumserver))
        capabilities = DesiredCapabilities.OPERA
        capabilities['opera.autostart'] = True
        capabilities['opera.arguments'] = '-fullscreen'
        return webdriver.Opera(seleniumserver, desired_capabilities=capabilities)

    def _setup_explorer(self):
        """
        Setup Internet Explorer webdriver
        """
        explorerdriver = self.config.get('Browser', 'explorerdriver_path')
        self.logger.debug("Explorer driver path given in properties: {0}".format(explorerdriver))
        return webdriver.Ie(explorerdriver)

    def _setup_phantomjs(self):
        """
        Setup phantomjs webdriver
        """
        phantomdriver = self.config.get('Browser', 'phantomdriver_path')
        self.logger.debug("Phantom driver path given in properties: {0}".format(phantomdriver))
        return webdriver.PhantomJS(executable_path=phantomdriver)

    def _setup_appium(self):
        """
        Setup Android webdriver
        """
        self.config.set('Server', 'host', '127.0.0.1')
        self.config.set('Server', 'port', '4723')
        return self._create_remotedriver()
