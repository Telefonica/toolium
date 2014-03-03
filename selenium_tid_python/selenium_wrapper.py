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
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium_tid_python.config import Config
import logging
import os
import datetime


class SeleniumWrapper(object):
    # Singleton instance
    _instance = None
    driver = None
    logger = None
    config = None
    screenshots_path = None
    screenshots_number = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            # Configure logger
            Config().initialize_logger()
            cls.logger = logging.getLogger(__name__)

            # Configure properties
            cls.config = Config().initialize_config()

            # Unique screenshots directory
            date = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
            browser_info = cls.config.get('Browser', 'browser').replace('-', '_')
            cls.screenshots_path = os.path.join(os.getcwd(), 'dist', 'screenshots', date + '_' + browser_info)
            cls.screenshots_number = 1

            # Create new instance
            cls._instance = super(SeleniumWrapper, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def _get_system_properties(self):
        '''
        Update all config properties values with system property values
        '''
        for section in self.config.sections:
            for option in self.config.options(section):
                self._get_system_property(section, option)

    def _get_system_property(self, section, option):
        '''
        Update a config property value with system property value
        '''
        try:
            propertyName = "{0}_{1}".format(section, option)
            self.config.set(section, option, os.environ[propertyName])
        except KeyError:
            pass

    def connect(self):
        """
        Set up the browser driver
        """
        if self.config.getboolean_optional('Server', 'enabled'):
            self._setup_remotedriver()
        else:
            self._setup_localdriver()

        return self.driver

    def _setup_remotedriver(self):
        """
        Setup webdriver in a remote server
        """
        browser = self.config.get('Browser', 'browser')
        self.logger.info("Creating remote driver (browser = {0})".format(browser))

        server_host = self.config.get('Server', 'host')
        server_port = self.config.get('Server', 'port')
        self._setup_remotedriver_common(browser, server_host, server_port)

    def _setup_remotedriver_common(self, browser, server_host, server_port):
        """
        Setup webdriver in a remote server
        """
        server_url = 'http://{0}:{1}/wd/hub'.format(server_host, server_port)

        # Get browser type capabilities
        capabilities_list = {
                             'firefox': DesiredCapabilities.FIREFOX,
                             'chrome': DesiredCapabilities.CHROME,
                             'safari': DesiredCapabilities.SAFARI,
                             'opera': DesiredCapabilities.OPERA,
                             'iexplore': DesiredCapabilities.INTERNETEXPLORER,
                             'phantomjs': DesiredCapabilities.PHANTOMJS,
                             'android': DesiredCapabilities.ANDROID,
                             'iphone': DesiredCapabilities.IPHONE,
                            }
        browser_name = browser.split('-')[0]
        capabilities = capabilities_list.get(browser_name)

        # Add browser version
        try:
            capabilities['version'] = browser.split('-')[1]
        except IndexError:
            pass

        # Add platform capability
        try:
            platforms_list = {
                              'xp': 'XP',
                              'windows_7': 'VISTA',
                              'windows_8': 'WIN8',
                              'linux': 'LINUX',
                              'mac': 'MAC',
                             }
            capabilities['platform'] = platforms_list.get(browser.split('-')[3])
        except IndexError:
            pass

        if browser_name == 'android' or browser_name == 'iphone':
            # Add Appium server capabilities
            for cap, cap_value in dict(self.config.items('AppiumCapabilities')).iteritems():
                self.logger.debug("Added server capability: {0} = {1}".format(cap, cap_value))
                capabilities[cap] = cap_value

        if browser_name == 'opera':
            capabilities['opera.autostart'] = True
            capabilities['opera.arguments'] = '-fullscreen'

        # Create remote driver
        self.driver = webdriver.Remote(command_executor=server_url, desired_capabilities=capabilities)

    def _setup_localdriver(self):
        """
        Setup webdriver in local machine
        """
        browser = self.config.get('Browser', 'browser')
        browser_name = browser.split('-')[0]
        self.logger.info("Creating local driver (browser = {0})".format(browser))

        def unknown_driver():
            assert False, 'Unknown driver {0}'.format(browser_name)

        browser_config = {
                          'firefox': self._setup_firefox,
                          'chrome': self._setup_chrome,
                          'safari': self._setup_safari,
                          'opera': self._setup_opera,
                          'iexplore': self._setup_explorer,
                          'phantomjs': self._setup_phantomjs,
                          'android': self._setup_appium,
                          'iphone': self._setup_appium,
                         }

        try:
            browser_config.get(browser_name, unknown_driver)()
        except Exception as exc:
            message = "{0} driver can not be launched: {1}".format(browser_name.title(), exc)
            self.logger.error(message)
            assert False, message

    def _setup_firefox(self):
        """
        Setup Firefox webdriver
        """
        profile = webdriver.FirefoxProfile()
        profile.native_events_enabled = True
        self.driver = webdriver.Firefox(firefox_profile=profile)

    def _setup_chrome(self):
        """
        Setup Chrome webdriver
        """
        chromedriver = self.config.get('Browser', 'chromedriver_path')
        self.logger.debug("Chrome driver path given in properties: {0}".format(chromedriver))
        options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(chromedriver, chrome_options=options)

    def _setup_safari(self):
        """
        Setup Safari webdriver
        """
        self.driver = webdriver.Safari()

    def _setup_opera(self):
        """
        Setup Opera webdriver
        """
        seleniumserver = self.config.get('Browser', 'seleniumserver_path')
        self.logger.debug("Selenium server path given in properties: {0}".format(seleniumserver))
        capabilities = DesiredCapabilities.OPERA
        capabilities['opera.autostart'] = True
        capabilities['opera.arguments'] = '-fullscreen'
        self.driver = webdriver.Opera(seleniumserver, desired_capabilities=capabilities)

    def _setup_explorer(self):
        """
        Setup Internet Explorer webdriver
        """
        explorerdriver = self.config.get('Browser', 'explorerdriver_path')
        self.logger.debug("Explorer driver path given in properties: {0}".format(explorerdriver))
        self.driver = webdriver.Ie(explorerdriver)

    def _setup_phantomjs(self):
        """
        Setup phantomjs webdriver
        """
        phantomdriver = self.config.get('Browser', 'phantomdriver_path')
        self.logger.debug("Phantom driver path given in properties: {0}".format(phantomdriver))
        self.driver = webdriver.PhantomJS(executable_path=phantomdriver)

    def _setup_appium(self):
        """
        Setup Android webdriver
        """
        browser = self.config.get('Browser', 'browser')
        server_host = '127.0.0.1'
        server_port = '4723'
        self._setup_remotedriver_common(browser, server_host, server_port)

    def is_mobile_test(self):
        '''
        Returns true if the tests must be executed in a mobile
        '''
        browser_name = self.config.get('Browser', 'browser').split('-')[0]
        return browser_name in ('android', 'iphone')

    def is_web_test(self):
        '''
        Returns true if the tests must be executed in a browser
        '''
        appium_app = self.config.get_optional('AppiumCapabilities', 'app')
        return not self.is_mobile_test() or appium_app in ('chrome', 'safari')

    def is_maximizable(self):
        '''
        Returns true if the browser is maximizable
        '''
        browser_name = self.config.get('Browser', 'browser').split('-')[0]
        return not self.is_mobile_test() and browser_name != 'opera'
