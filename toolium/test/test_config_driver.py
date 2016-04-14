# -*- coding: utf-8 -*-
u"""
Copyright 2016 Telefónica Investigación y Desarrollo, S.A.U.
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

import unittest

import mock
from nose.tools import assert_equal, assert_raises
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from toolium.config_driver import ConfigDriver
from toolium.config_parser import ExtendedConfigParser


class ConfigDriverTests(unittest.TestCase):
    """
    :type config: toolium.config_parser.ExtendedConfigParser or configparser.ConfigParser
    """

    def setUp(self):
        self.config = ExtendedConfigParser()
        self.config.add_section('Server')
        self.config.add_section('Driver')

    def test_create_driver_local_not_configured(self):
        self.config.set('Driver', 'type', 'firefox')
        config_driver = ConfigDriver(self.config)
        config_driver._create_local_driver = lambda: 'local driver mock'
        config_driver._create_remote_driver = lambda: 'remote driver mock'

        driver = config_driver.create_driver()

        assert_equal(driver, 'local driver mock')

    def test_create_driver_local(self):
        self.config.set('Server', 'enabled', 'false')
        self.config.set('Driver', 'type', 'firefox')
        config_driver = ConfigDriver(self.config)
        config_driver._create_local_driver = lambda: 'local driver mock'
        config_driver._create_remote_driver = lambda: 'remote driver mock'

        driver = config_driver.create_driver()

        assert_equal(driver, 'local driver mock')

    def test_create_driver_remote(self):
        self.config.set('Server', 'enabled', 'true')
        self.config.set('Driver', 'type', 'firefox')
        config_driver = ConfigDriver(self.config)
        config_driver._create_local_driver = lambda: 'local driver mock'
        config_driver._create_remote_driver = lambda: 'remote driver mock'

        driver = config_driver.create_driver()

        assert_equal(driver, 'remote driver mock')

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_local_driver_firefox(self, webdriver_mock):
        self.config.set('Driver', 'type', 'firefox')
        config_driver = ConfigDriver(self.config)
        config_driver._create_firefox_profile = lambda: 'firefox profile'

        config_driver._create_local_driver()
        webdriver_mock.Firefox.assert_called_with(capabilities=DesiredCapabilities.FIREFOX,
                                                  firefox_profile='firefox profile')

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_local_driver_chrome(self, webdriver_mock):
        self.config.set('Driver', 'type', 'chrome')
        self.config.set('Driver', 'chrome_driver_path', '/tmp/driver')
        config_driver = ConfigDriver(self.config)
        config_driver._create_chrome_options = lambda: 'chrome options'

        config_driver._create_local_driver()
        webdriver_mock.Chrome.assert_called_with('/tmp/driver', desired_capabilities=DesiredCapabilities.CHROME,
                                                 chrome_options='chrome options')

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_local_driver_safari(self, webdriver_mock):
        self.config.set('Driver', 'type', 'safari')
        config_driver = ConfigDriver(self.config)

        config_driver._create_local_driver()
        webdriver_mock.Safari.assert_called_with(desired_capabilities=DesiredCapabilities.SAFARI)

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_local_driver_opera(self, webdriver_mock):
        self.config.set('Driver', 'type', 'opera')
        self.config.set('Driver', 'opera_driver_path', '/tmp/driver')
        config_driver = ConfigDriver(self.config)

        config_driver._create_local_driver()
        webdriver_mock.Opera.assert_called_with(desired_capabilities=DesiredCapabilities.OPERA,
                                                executable_path='/tmp/driver')

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_local_driver_iexplore(self, webdriver_mock):
        self.config.set('Driver', 'type', 'iexplore')
        self.config.set('Driver', 'explorer_driver_path', '/tmp/driver')
        config_driver = ConfigDriver(self.config)

        config_driver._create_local_driver()
        webdriver_mock.Ie.assert_called_with('/tmp/driver', capabilities=DesiredCapabilities.INTERNETEXPLORER)

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_local_driver_edge(self, webdriver_mock):
        self.config.set('Driver', 'type', 'edge')
        self.config.set('Driver', 'edge_driver_path', '/tmp/driver')
        config_driver = ConfigDriver(self.config)

        config_driver._create_local_driver()
        webdriver_mock.Edge.assert_called_with('/tmp/driver', capabilities=DesiredCapabilities.EDGE)

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_local_driver_phantomjs(self, webdriver_mock):
        self.config.set('Driver', 'type', 'phantomjs')
        self.config.set('Driver', 'phantomjs_driver_path', '/tmp/driver')
        config_driver = ConfigDriver(self.config)

        config_driver._create_local_driver()
        webdriver_mock.PhantomJS.assert_called_with(desired_capabilities=DesiredCapabilities.PHANTOMJS,
                                                    executable_path='/tmp/driver')

    def test_create_local_driver_android(self):
        self.config.set('Driver', 'type', 'android')
        config_driver = ConfigDriver(self.config)
        config_driver._create_remote_driver = lambda: 'remote driver mock'

        driver = config_driver._create_local_driver()
        assert_equal(driver, 'remote driver mock')

    def test_create_local_driver_ios(self):
        self.config.set('Driver', 'type', 'ios')
        config_driver = ConfigDriver(self.config)
        config_driver._create_remote_driver = lambda: 'remote driver mock'

        driver = config_driver._create_local_driver()
        assert_equal(driver, 'remote driver mock')

    def test_create_local_driver_iphone(self):
        self.config.set('Driver', 'type', 'iphone')
        config_driver = ConfigDriver(self.config)
        config_driver._create_remote_driver = lambda: 'remote driver mock'

        driver = config_driver._create_local_driver()
        assert_equal(driver, 'remote driver mock')

    def test_create_local_driver_unknown_driver(self):
        self.config.set('Driver', 'type', 'unknown')
        config_driver = ConfigDriver(self.config)

        with assert_raises(Exception) as cm:
            config_driver._create_local_driver()
        assert_equal('Unknown driver unknown', str(cm.exception))

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_local_driver_capabilities(self, webdriver_mock):
        self.config.set('Driver', 'type', 'firefox')
        self.config.add_section('Capabilities')
        self.config.set('Capabilities', 'version', '45')
        config_driver = ConfigDriver(self.config)
        config_driver._create_firefox_profile = lambda: 'firefox profile'

        config_driver._create_local_driver()
        capabilities = DesiredCapabilities.FIREFOX
        capabilities['version'] = '45'
        webdriver_mock.Firefox.assert_called_with(capabilities=capabilities,
                                                  firefox_profile='firefox profile')

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_remote_driver_firefox(self, webdriver_mock):
        self.config.set('Server', 'host', '10.20.30.40')
        self.config.set('Server', 'port', '5555')
        self.config.set('Driver', 'type', 'firefox')
        config_driver = ConfigDriver(self.config)

        # Firefox profile mock
        class ProfileMock(object):
            encoded = 'encoded profile'
        config_driver._create_firefox_profile = mock.MagicMock(return_value=ProfileMock())

        config_driver._create_remote_driver()
        capabilities = DesiredCapabilities.FIREFOX
        capabilities['firefox_profile'] = 'encoded profile'
        webdriver_mock.Remote.assert_called_with(command_executor='http://10.20.30.40:5555/wd/hub',
                                                 desired_capabilities=capabilities)

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_remote_driver_chrome(self, webdriver_mock):
        self.config.set('Server', 'host', '10.20.30.40')
        self.config.set('Server', 'port', '5555')
        self.config.set('Driver', 'type', 'chrome')
        config_driver = ConfigDriver(self.config)

        # Chrome options mock
        chrome_options = mock.MagicMock()
        chrome_options.to_capabilities.return_value = {'chromeOptions': 'chrome options'}
        config_driver._create_chrome_options = mock.MagicMock(return_value=chrome_options)

        config_driver._create_remote_driver()
        capabilities = DesiredCapabilities.CHROME
        capabilities['chromeOptions'] = 'chrome options'
        webdriver_mock.Remote.assert_called_with(command_executor='http://10.20.30.40:5555/wd/hub',
                                                 desired_capabilities=capabilities)

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_remote_driver_safari(self, webdriver_mock):
        self.config.set('Server', 'host', '10.20.30.40')
        self.config.set('Server', 'port', '5555')
        self.config.set('Driver', 'type', 'safari')
        config_driver = ConfigDriver(self.config)

        config_driver._create_remote_driver()
        capabilities = DesiredCapabilities.SAFARI
        webdriver_mock.Remote.assert_called_with(command_executor='http://10.20.30.40:5555/wd/hub',
                                                 desired_capabilities=capabilities)

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_remote_driver_opera(self, webdriver_mock):
        self.config.set('Server', 'host', '10.20.30.40')
        self.config.set('Server', 'port', '5555')
        self.config.set('Driver', 'type', 'opera')
        config_driver = ConfigDriver(self.config)

        config_driver._create_remote_driver()
        capabilities = DesiredCapabilities.OPERA
        capabilities['opera.autostart'] = True
        capabilities['opera.arguments'] = '-fullscreen'
        webdriver_mock.Remote.assert_called_with(command_executor='http://10.20.30.40:5555/wd/hub',
                                                 desired_capabilities=capabilities)

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_remote_driver_iexplore(self, webdriver_mock):
        self.config.set('Server', 'host', '10.20.30.40')
        self.config.set('Server', 'port', '5555')
        self.config.set('Driver', 'type', 'iexplore')
        config_driver = ConfigDriver(self.config)

        config_driver._create_remote_driver()
        capabilities = DesiredCapabilities.INTERNETEXPLORER
        webdriver_mock.Remote.assert_called_with(command_executor='http://10.20.30.40:5555/wd/hub',
                                                 desired_capabilities=capabilities)

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_remote_driver_edge(self, webdriver_mock):
        self.config.set('Server', 'host', '10.20.30.40')
        self.config.set('Server', 'port', '5555')
        self.config.set('Driver', 'type', 'edge')
        config_driver = ConfigDriver(self.config)

        config_driver._create_remote_driver()
        capabilities = DesiredCapabilities.EDGE
        webdriver_mock.Remote.assert_called_with(command_executor='http://10.20.30.40:5555/wd/hub',
                                                 desired_capabilities=capabilities)

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_remote_driver_phantomjs(self, webdriver_mock):
        self.config.set('Server', 'host', '10.20.30.40')
        self.config.set('Server', 'port', '5555')
        self.config.set('Driver', 'type', 'phantomjs')
        config_driver = ConfigDriver(self.config)

        config_driver._create_remote_driver()
        capabilities = DesiredCapabilities.PHANTOMJS
        webdriver_mock.Remote.assert_called_with(command_executor='http://10.20.30.40:5555/wd/hub',
                                                 desired_capabilities=capabilities)

    @mock.patch('toolium.config_driver.appiumdriver')
    def test_create_remote_driver_android(self, appiumdriver_mock):
        self.config.set('Server', 'host', '10.20.30.40')
        self.config.set('Server', 'port', '5555')
        self.config.set('Driver', 'type', 'android')
        self.config.add_section('AppiumCapabilities')
        self.config.set('AppiumCapabilities', 'automationName', 'Appium')
        self.config.set('AppiumCapabilities', 'platformName', 'Android')
        config_driver = ConfigDriver(self.config)

        config_driver._create_remote_driver()
        capabilities = {'automationName': 'Appium', 'platformName': 'Android'}
        appiumdriver_mock.Remote.assert_called_with(command_executor='http://10.20.30.40:5555/wd/hub',
                                                    desired_capabilities=capabilities)

    @mock.patch('toolium.config_driver.appiumdriver')
    def test_create_remote_driver_ios(self, appiumdriver_mock):
        self.config.set('Server', 'host', '10.20.30.40')
        self.config.set('Server', 'port', '5555')
        self.config.set('Driver', 'type', 'ios')
        self.config.add_section('AppiumCapabilities')
        self.config.set('AppiumCapabilities', 'automationName', 'Appium')
        self.config.set('AppiumCapabilities', 'platformName', 'iOS')
        config_driver = ConfigDriver(self.config)

        config_driver._create_remote_driver()
        capabilities = {'automationName': 'Appium', 'platformName': 'iOS'}
        appiumdriver_mock.Remote.assert_called_with(command_executor='http://10.20.30.40:5555/wd/hub',
                                                    desired_capabilities=capabilities)

    @mock.patch('toolium.config_driver.appiumdriver')
    def test_create_remote_driver_iphone(self, appiumdriver_mock):
        self.config.set('Server', 'host', '10.20.30.40')
        self.config.set('Server', 'port', '5555')
        self.config.set('Driver', 'type', 'iphone')
        self.config.add_section('AppiumCapabilities')
        self.config.set('AppiumCapabilities', 'automationName', 'Appium')
        self.config.set('AppiumCapabilities', 'platformName', 'iOS')
        config_driver = ConfigDriver(self.config)

        config_driver._create_remote_driver()
        capabilities = {'automationName': 'Appium', 'platformName': 'iOS'}
        appiumdriver_mock.Remote.assert_called_with(command_executor='http://10.20.30.40:5555/wd/hub',
                                                    desired_capabilities=capabilities)

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_remote_driver_version_platform(self, webdriver_mock):
        self.config.set('Server', 'host', '10.20.30.40')
        self.config.set('Server', 'port', '5555')
        self.config.set('Driver', 'type', 'iexplore-11-on-WIN10')
        config_driver = ConfigDriver(self.config)

        config_driver._create_remote_driver()
        capabilities = DesiredCapabilities.INTERNETEXPLORER
        capabilities['version'] = '11'
        capabilities['platform'] = 'WIN10'
        webdriver_mock.Remote.assert_called_with(command_executor='http://10.20.30.40:5555/wd/hub',
                                                 desired_capabilities=capabilities)

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_remote_driver_version(self, webdriver_mock):
        self.config.set('Server', 'host', '10.20.30.40')
        self.config.set('Server', 'port', '5555')
        self.config.set('Driver', 'type', 'iexplore-11')
        config_driver = ConfigDriver(self.config)

        config_driver._create_remote_driver()
        capabilities = DesiredCapabilities.INTERNETEXPLORER
        capabilities['version'] = '11'
        webdriver_mock.Remote.assert_called_with(command_executor='http://10.20.30.40:5555/wd/hub',
                                                 desired_capabilities=capabilities)

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_remote_driver_capabilities(self, webdriver_mock):
        self.config.set('Server', 'host', '10.20.30.40')
        self.config.set('Server', 'port', '5555')
        self.config.set('Driver', 'type', 'iexplore-11')
        self.config.add_section('Capabilities')
        self.config.set('Capabilities', 'version', '11')
        config_driver = ConfigDriver(self.config)

        config_driver._create_remote_driver()
        capabilities = DesiredCapabilities.INTERNETEXPLORER
        capabilities['version'] = '11'
        webdriver_mock.Remote.assert_called_with(command_executor='http://10.20.30.40:5555/wd/hub',
                                                 desired_capabilities=capabilities)

    def test_convert_property_type_true(self):
        config_driver = ConfigDriver(self.config)
        value = 'True'
        assert_equal(config_driver._convert_property_type(value), True)

    def test_convert_property_type_false(self):
        config_driver = ConfigDriver(self.config)
        value = 'False'
        assert_equal(config_driver._convert_property_type(value), False)

    def test_convert_property_type_dict(self):
        config_driver = ConfigDriver(self.config)
        value = "{'a': 5}"
        assert_equal(config_driver._convert_property_type(value), {'a': 5})

    def test_convert_property_type_int(self):
        config_driver = ConfigDriver(self.config)
        value = '5'
        assert_equal(config_driver._convert_property_type(value), 5)

    def test_convert_property_type_str(self):
        config_driver = ConfigDriver(self.config)
        value = 'string'
        assert_equal(config_driver._convert_property_type(value), value)

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_firefox_profile(self, webdriver_mock):
        self.config.add_section('Firefox')
        self.config.set('Firefox', 'profile', '/tmp')
        self.config.add_section('FirefoxPreferences')
        self.config.set('FirefoxPreferences', 'browser.download.folderList', '2')
        self.config.add_section('FirefoxExtensions')
        self.config.set('FirefoxExtensions', 'firebug', 'resources/firebug-3.0.0-beta.3.xpi')
        config_driver = ConfigDriver(self.config)

        config_driver._create_firefox_profile()
        webdriver_mock.FirefoxProfile.assert_called_with(profile_directory='/tmp')
        webdriver_mock.FirefoxProfile().set_preference.assert_called_with('browser.download.folderList', 2)
        webdriver_mock.FirefoxProfile().update_preferences.assert_called_with()
        webdriver_mock.FirefoxProfile().add_extension.assert_called_with('resources/firebug-3.0.0-beta.3.xpi')

    @mock.patch('toolium.config_driver.webdriver')
    def test_create_chrome_options(self, webdriver_mock):
        self.config.add_section('ChromePreferences')
        self.config.set('ChromePreferences', 'download.default_directory', '/tmp')
        self.config.add_section('ChromeMobileEmulation')
        self.config.set('ChromeMobileEmulation', 'deviceName', 'Google Nexus 5')
        self.config.add_section('ChromeArguments')
        self.config.set('ChromeArguments', 'lang', 'es')
        config_driver = ConfigDriver(self.config)

        config_driver._create_chrome_options()
        webdriver_mock.ChromeOptions.assert_called_with()
        webdriver_mock.ChromeOptions().add_experimental_option.assert_has_calls(
            [mock.call('prefs', {'download.default_directory': '/tmp'}),
             mock.call('mobileEmulation', {'deviceName': 'Google Nexus 5'})])
        webdriver_mock.ChromeOptions().add_argument.assert_called_with('lang=es')
