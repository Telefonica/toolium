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

import mock
import os
import pytest
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.options import Options

from toolium.config_driver import ConfigDriver
from toolium.config_parser import ExtendedConfigParser
from toolium.driver_wrappers_pool import DriverWrappersPool


@pytest.fixture
def config():
    config_parser = ExtendedConfigParser()
    config_parser.add_section('Server')
    config_parser.add_section('Driver')
    return config_parser


@pytest.fixture
def utils():
    utils = mock.MagicMock()
    utils.get_driver_name.return_value = 'firefox'
    return utils


def test_create_driver_local_not_configured(config, utils):
    config.set('Driver', 'type', 'firefox')
    utils.get_driver_name.return_value = 'firefox'
    config_driver = ConfigDriver(config, utils)
    config_driver._create_local_driver = lambda: 'local driver mock'
    config_driver._create_remote_driver = lambda: 'remote driver mock'

    driver = config_driver.create_driver()

    assert driver == 'local driver mock'


def test_create_driver_local(config, utils):
    config.set('Server', 'enabled', 'false')
    config.set('Driver', 'type', 'firefox')
    utils.get_driver_name.return_value = 'firefox'
    config_driver = ConfigDriver(config, utils)
    config_driver._create_local_driver = lambda: 'local driver mock'
    config_driver._create_remote_driver = lambda: 'remote driver mock'

    driver = config_driver.create_driver()

    assert driver == 'local driver mock'


def test_create_driver_remote(config, utils):
    config.set('Server', 'enabled', 'true')
    config.set('Driver', 'type', 'firefox')
    utils.get_driver_name.return_value = 'firefox'
    config_driver = ConfigDriver(config, utils)
    config_driver._create_local_driver = lambda: 'local driver mock'
    config_driver._create_remote_driver = lambda: 'remote driver mock'

    driver = config_driver.create_driver()

    assert driver == 'remote driver mock'


@mock.patch('toolium.config_driver.Options')
@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_firefox(webdriver_mock, options, config, utils):
    config.set('Driver', 'type', 'firefox')
    config.add_section('Capabilities')
    config.set('Capabilities', 'marionette', 'false')
    utils.get_driver_name.return_value = 'firefox'
    config_driver = ConfigDriver(config, utils)
    config_driver._create_firefox_profile = lambda: 'firefox profile'
    DriverWrappersPool.output_directory = ''

    config_driver._create_local_driver()
    expected_capabilities = DesiredCapabilities.FIREFOX.copy()
    expected_capabilities['marionette'] = False
    webdriver_mock.Firefox.assert_called_once_with(capabilities=expected_capabilities,
                                                   firefox_profile='firefox profile', executable_path=None,
                                                   firefox_options=options(), log_path='geckodriver.log')


@mock.patch('toolium.config_driver.Options')
@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_firefox_gecko(webdriver_mock, options, config, utils):
    config.set('Driver', 'type', 'firefox')
    config.add_section('Capabilities')
    config.set('Capabilities', 'marionette', 'true')
    config.set('Driver', 'gecko_driver_path', '/tmp/driver')
    utils.get_driver_name.return_value = 'firefox'
    config_driver = ConfigDriver(config, utils)
    config_driver._create_firefox_profile = lambda: 'firefox profile'
    DriverWrappersPool.output_directory = ''

    config_driver._create_local_driver()
    expected_capabilities = DesiredCapabilities.FIREFOX.copy()
    expected_capabilities['marionette'] = True
    webdriver_mock.Firefox.assert_called_once_with(capabilities=expected_capabilities,
                                                   firefox_profile='firefox profile', executable_path='/tmp/driver',
                                                   firefox_options=options(), log_path='geckodriver.log')


@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_firefox_binary(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'firefox')
    config.add_section('Capabilities')
    config.set('Capabilities', 'marionette', 'false')
    config.add_section('Firefox')
    config.set('Firefox', 'binary', '/tmp/firefox')
    utils.get_driver_name.return_value = 'firefox'
    config_driver = ConfigDriver(config, utils)
    config_driver._create_firefox_profile = lambda: 'firefox profile'
    DriverWrappersPool.output_directory = ''

    config_driver._create_local_driver()

    # Check that firefox options contain the firefox binary
    args, kwargs = webdriver_mock.Firefox.call_args
    firefox_options = kwargs['firefox_options']
    assert isinstance(firefox_options, Options)
    if isinstance(firefox_options.binary, str):
        assert firefox_options.binary == '/tmp/firefox'  # Selenium 2
    else:
        assert firefox_options.binary._start_cmd == '/tmp/firefox'  # Selenium 3


@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_chrome(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'chrome')
    config.set('Driver', 'chrome_driver_path', '/tmp/driver')
    utils.get_driver_name.return_value = 'chrome'
    config_driver = ConfigDriver(config, utils)
    config_driver._create_chrome_options = lambda: 'chrome options'

    config_driver._create_local_driver()
    webdriver_mock.Chrome.assert_called_once_with('/tmp/driver', desired_capabilities=DesiredCapabilities.CHROME,
                                                  chrome_options='chrome options')


@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_safari(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'safari')
    utils.get_driver_name.return_value = 'safari'
    config_driver = ConfigDriver(config, utils)

    config_driver._create_local_driver()
    webdriver_mock.Safari.assert_called_once_with(desired_capabilities=DesiredCapabilities.SAFARI)


@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_opera(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'opera')
    config.set('Driver', 'opera_driver_path', '/tmp/driver')
    utils.get_driver_name.return_value = 'opera'
    config_driver = ConfigDriver(config, utils)

    config_driver._create_local_driver()
    webdriver_mock.Opera.assert_called_once_with(desired_capabilities=DesiredCapabilities.OPERA,
                                                 executable_path='/tmp/driver')


@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_iexplore(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'iexplore')
    config.set('Driver', 'explorer_driver_path', '/tmp/driver')
    utils.get_driver_name.return_value = 'iexplore'
    config_driver = ConfigDriver(config, utils)

    config_driver._create_local_driver()
    webdriver_mock.Ie.assert_called_once_with('/tmp/driver', capabilities=DesiredCapabilities.INTERNETEXPLORER)


@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_edge(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'edge')
    config.set('Driver', 'edge_driver_path', '/tmp/driver')
    utils.get_driver_name.return_value = 'edge'
    config_driver = ConfigDriver(config, utils)

    config_driver._create_local_driver()
    webdriver_mock.Edge.assert_called_once_with('/tmp/driver', capabilities=DesiredCapabilities.EDGE)


@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_phantomjs(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'phantomjs')
    config.set('Driver', 'phantomjs_driver_path', '/tmp/driver')
    utils.get_driver_name.return_value = 'phantomjs'
    config_driver = ConfigDriver(config, utils)

    config_driver._create_local_driver()
    webdriver_mock.PhantomJS.assert_called_once_with(desired_capabilities=DesiredCapabilities.PHANTOMJS,
                                                     executable_path='/tmp/driver')


def test_create_local_driver_android(config, utils):
    config.set('Driver', 'type', 'android')
    utils.get_driver_name.return_value = 'android'
    config_driver = ConfigDriver(config, utils)
    config_driver._create_remote_driver = lambda: 'remote driver mock'

    driver = config_driver._create_local_driver()
    assert driver == 'remote driver mock'


def test_create_local_driver_ios(config, utils):
    config.set('Driver', 'type', 'ios')
    utils.get_driver_name.return_value = 'ios'
    config_driver = ConfigDriver(config, utils)
    config_driver._create_remote_driver = lambda: 'remote driver mock'

    driver = config_driver._create_local_driver()
    assert driver == 'remote driver mock'


def test_create_local_driver_iphone(config, utils):
    config.set('Driver', 'type', 'iphone')
    utils.get_driver_name.return_value = 'iphone'
    config_driver = ConfigDriver(config, utils)
    config_driver._create_remote_driver = lambda: 'remote driver mock'

    driver = config_driver._create_local_driver()
    assert driver == 'remote driver mock'


def test_create_local_driver_unknown_driver(config, utils):
    config.set('Driver', 'type', 'unknown')
    utils.get_driver_name.return_value = 'unknown'
    config_driver = ConfigDriver(config, utils)

    with pytest.raises(Exception) as excinfo:
        config_driver._create_local_driver()
    assert 'Unknown driver unknown' == str(excinfo.value)


@mock.patch('toolium.config_driver.Options')
@mock.patch('toolium.config_driver.webdriver')
def test_create_local_driver_capabilities(webdriver_mock, options, config, utils):
    config.set('Driver', 'type', 'firefox')
    config.add_section('Capabilities')
    config.set('Capabilities', 'marionette', 'false')
    config.set('Capabilities', 'version', '45')
    utils.get_driver_name.return_value = 'firefox'
    config_driver = ConfigDriver(config, utils)
    config_driver._create_firefox_profile = lambda: 'firefox profile'
    DriverWrappersPool.output_directory = ''

    config_driver._create_local_driver()
    expected_capabilities = DesiredCapabilities.FIREFOX.copy()
    expected_capabilities['marionette'] = False
    expected_capabilities['version'] = '45'
    webdriver_mock.Firefox.assert_called_once_with(capabilities=expected_capabilities,
                                                   firefox_profile='firefox profile', executable_path=None,
                                                   firefox_options=options(), log_path='geckodriver.log')


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_firefox(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'firefox')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    utils.get_driver_name.return_value = 'firefox'
    config_driver = ConfigDriver(config, utils)

    # Firefox profile mock
    class ProfileMock(object):
        encoded = 'encoded profile'

    config_driver._create_firefox_profile = mock.MagicMock(return_value=ProfileMock())

    config_driver._create_remote_driver()
    capabilities = DesiredCapabilities.FIREFOX.copy()
    capabilities['firefox_profile'] = 'encoded profile'
    webdriver_mock.Remote.assert_called_once_with(command_executor='%s/wd/hub' % server_url,
                                                  desired_capabilities=capabilities)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_chrome(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'chrome')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    utils.get_driver_name.return_value = 'chrome'
    config_driver = ConfigDriver(config, utils)

    # Chrome options mock
    chrome_options = mock.MagicMock()
    chrome_options.to_capabilities.return_value = {'goog:chromeOptions': 'chrome options'}
    config_driver._create_chrome_options = mock.MagicMock(return_value=chrome_options)

    config_driver._create_remote_driver()
    capabilities = DesiredCapabilities.CHROME.copy()
    capabilities['goog:chromeOptions'] = 'chrome options'
    webdriver_mock.Remote.assert_called_once_with(command_executor='%s/wd/hub' % server_url,
                                                  desired_capabilities=capabilities)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_chrome_old_selenium(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'chrome')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    utils.get_driver_name.return_value = 'chrome'
    config_driver = ConfigDriver(config, utils)

    # Chrome options mock
    chrome_options = mock.MagicMock()
    chrome_options.to_capabilities.return_value = {'chromeOptions': 'chrome options'}
    config_driver._create_chrome_options = mock.MagicMock(return_value=chrome_options)

    config_driver._create_remote_driver()
    capabilities = DesiredCapabilities.CHROME.copy()
    capabilities['chromeOptions'] = 'chrome options'
    webdriver_mock.Remote.assert_called_once_with(command_executor='%s/wd/hub' % server_url,
                                                  desired_capabilities=capabilities)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_safari(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'safari')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    utils.get_driver_name.return_value = 'safari'
    config_driver = ConfigDriver(config, utils)

    config_driver._create_remote_driver()
    webdriver_mock.Remote.assert_called_once_with(command_executor='%s/wd/hub' % server_url,
                                                  desired_capabilities=DesiredCapabilities.SAFARI)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_opera(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'opera')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    utils.get_driver_name.return_value = 'opera'
    config_driver = ConfigDriver(config, utils)

    config_driver._create_remote_driver()
    capabilities = DesiredCapabilities.OPERA
    capabilities['opera.autostart'] = True
    capabilities['opera.arguments'] = '-fullscreen'
    webdriver_mock.Remote.assert_called_once_with(command_executor='%s/wd/hub' % server_url,
                                                  desired_capabilities=capabilities)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_iexplore(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'iexplore')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    utils.get_driver_name.return_value = 'iexplore'
    config_driver = ConfigDriver(config, utils)

    config_driver._create_remote_driver()
    webdriver_mock.Remote.assert_called_once_with(command_executor='%s/wd/hub' % server_url,
                                                  desired_capabilities=DesiredCapabilities.INTERNETEXPLORER)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_edge(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'edge')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    utils.get_driver_name.return_value = 'edge'
    config_driver = ConfigDriver(config, utils)

    config_driver._create_remote_driver()
    webdriver_mock.Remote.assert_called_once_with(command_executor='%s/wd/hub' % server_url,
                                                  desired_capabilities=DesiredCapabilities.EDGE)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_phantomjs(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'phantomjs')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    utils.get_driver_name.return_value = 'phantomjs'
    config_driver = ConfigDriver(config, utils)

    config_driver._create_remote_driver()
    webdriver_mock.Remote.assert_called_once_with(command_executor='%s/wd/hub' % server_url,
                                                  desired_capabilities=DesiredCapabilities.PHANTOMJS)


@mock.patch('toolium.config_driver.appiumdriver')
def test_create_remote_driver_android(appiumdriver_mock, config, utils):
    config.set('Driver', 'type', 'android')
    config.add_section('AppiumCapabilities')
    config.set('AppiumCapabilities', 'automationName', 'Appium')
    config.set('AppiumCapabilities', 'platformName', 'Android')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    utils.get_driver_name.return_value = 'android'
    config_driver = ConfigDriver(config, utils)

    config_driver._create_remote_driver()
    capabilities = {'automationName': 'Appium', 'platformName': 'Android'}
    appiumdriver_mock.Remote.assert_called_once_with(command_executor='%s/wd/hub' % server_url,
                                                     desired_capabilities=capabilities)


@mock.patch('toolium.config_driver.appiumdriver')
def test_create_remote_driver_ios(appiumdriver_mock, config, utils):
    config.set('Driver', 'type', 'ios')
    config.add_section('AppiumCapabilities')
    config.set('AppiumCapabilities', 'automationName', 'Appium')
    config.set('AppiumCapabilities', 'platformName', 'iOS')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    utils.get_driver_name.return_value = 'ios'
    config_driver = ConfigDriver(config, utils)

    config_driver._create_remote_driver()
    capabilities = {'automationName': 'Appium', 'platformName': 'iOS'}
    appiumdriver_mock.Remote.assert_called_once_with(command_executor='%s/wd/hub' % server_url,
                                                     desired_capabilities=capabilities)


@mock.patch('toolium.config_driver.appiumdriver')
def test_create_remote_driver_iphone(appiumdriver_mock, config):
    config.set('Driver', 'type', 'iphone')
    config.add_section('AppiumCapabilities')
    config.set('AppiumCapabilities', 'automationName', 'Appium')
    config.set('AppiumCapabilities', 'platformName', 'iOS')
    server_url = 'http://10.20.30.40:5555'
    utils = mock.MagicMock()
    utils.get_server_url.return_value = server_url
    utils.get_driver_name.return_value = 'iphone'
    config_driver = ConfigDriver(config, utils)

    config_driver._create_remote_driver()
    capabilities = {'automationName': 'Appium', 'platformName': 'iOS'}
    appiumdriver_mock.Remote.assert_called_once_with(command_executor='%s/wd/hub' % server_url,
                                                     desired_capabilities=capabilities)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_version_platform(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'iexplore-11-on-WIN10')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    utils.get_driver_name.return_value = 'iexplore'
    config_driver = ConfigDriver(config, utils)

    config_driver._create_remote_driver()
    capabilities = DesiredCapabilities.INTERNETEXPLORER
    capabilities['version'] = '11'
    capabilities['platform'] = 'WIN10'
    webdriver_mock.Remote.assert_called_once_with(command_executor='%s/wd/hub' % server_url,
                                                  desired_capabilities=capabilities)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_version(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'iexplore-11')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    utils.get_driver_name.return_value = 'iexplore'
    config_driver = ConfigDriver(config, utils)

    config_driver._create_remote_driver()
    capabilities = DesiredCapabilities.INTERNETEXPLORER.copy()
    capabilities['version'] = '11'
    webdriver_mock.Remote.assert_called_once_with(command_executor='%s/wd/hub' % server_url,
                                                  desired_capabilities=capabilities)


@mock.patch('toolium.config_driver.webdriver')
def test_create_remote_driver_capabilities(webdriver_mock, config, utils):
    config.set('Driver', 'type', 'iexplore-11')
    config.add_section('Capabilities')
    config.set('Capabilities', 'version', '11')
    server_url = 'http://10.20.30.40:5555'
    utils.get_server_url.return_value = server_url
    utils.get_driver_name.return_value = 'iexplore'
    config_driver = ConfigDriver(config, utils)

    config_driver._create_remote_driver()
    capabilities = DesiredCapabilities.INTERNETEXPLORER.copy()
    capabilities['version'] = '11'
    webdriver_mock.Remote.assert_called_once_with(command_executor='%s/wd/hub' % server_url,
                                                  desired_capabilities=capabilities)


def test_convert_property_type_true(config, utils):
    config_driver = ConfigDriver(config, utils)
    value = 'True'
    assert config_driver._convert_property_type(value) is True


def test_convert_property_type_false(config, utils):
    config_driver = ConfigDriver(config, utils)
    value = 'False'
    assert config_driver._convert_property_type(value) is False


def test_convert_property_type_dict(config, utils):
    config_driver = ConfigDriver(config, utils)
    value = "{'a': 5}"
    assert config_driver._convert_property_type(value) == {'a': 5}


def test_convert_property_type_int(config, utils):
    config_driver = ConfigDriver(config, utils)
    value = '5'
    assert config_driver._convert_property_type(value) == 5


def test_convert_property_type_str(config, utils):
    config_driver = ConfigDriver(config, utils)
    value = 'string'
    assert config_driver._convert_property_type(value) == value


def test_convert_property_type_list(config, utils):
    config_driver = ConfigDriver(config, utils)
    value = "[1, 2, 3]"
    assert config_driver._convert_property_type(value) == [1, 2, 3]


@mock.patch('toolium.config_driver.webdriver')
def test_create_firefox_profile(webdriver_mock, config, utils):
    config.add_section('Firefox')
    config.set('Firefox', 'profile', '/tmp')
    config.add_section('FirefoxPreferences')
    config.set('FirefoxPreferences', 'browser.download.folderList', '2')
    config.add_section('FirefoxExtensions')
    config.set('FirefoxExtensions', 'firebug', 'resources/firebug-3.0.0-beta.3.xpi')
    config_driver = ConfigDriver(config, utils)

    config_driver._create_firefox_profile()
    webdriver_mock.FirefoxProfile.assert_called_once_with(profile_directory='/tmp')
    webdriver_mock.FirefoxProfile().set_preference.assert_called_once_with('browser.download.folderList', 2)
    webdriver_mock.FirefoxProfile().update_preferences.assert_called_once_with()
    webdriver_mock.FirefoxProfile().add_extension.assert_called_once_with('resources/firebug-3.0.0-beta.3.xpi')


def test_add_firefox_arguments(config, utils):
    config.add_section('FirefoxArguments')
    config.set('FirefoxArguments', '-private', '')
    config_driver = ConfigDriver(config, utils)
    firefox_options = Options()

    config_driver._add_firefox_arguments(firefox_options)
    assert firefox_options.arguments == ['-private']


@mock.patch('toolium.config_driver.webdriver')
def test_create_chrome_options(webdriver_mock, config, utils):
    config.add_section('ChromePreferences')
    config.set('ChromePreferences', 'download.default_directory', '/tmp')
    config.add_section('ChromeMobileEmulation')
    config.set('ChromeMobileEmulation', 'deviceName', 'Google Nexus 5')
    config.add_section('ChromeArguments')
    config.set('ChromeArguments', 'lang', 'es')
    config_driver = ConfigDriver(config, utils)

    config_driver._create_chrome_options()
    webdriver_mock.ChromeOptions.assert_called_once_with()
    webdriver_mock.ChromeOptions().add_experimental_option.assert_has_calls(
        [mock.call('prefs', {'download.default_directory': '/tmp'}),
         mock.call('mobileEmulation', {'deviceName': 'Google Nexus 5'})]
    )
    webdriver_mock.ChromeOptions().add_argument.assert_called_once_with('lang=es')


@mock.patch('toolium.config_driver.webdriver')
def test_create_chrome_options_headless(webdriver_mock, config, utils):
    config.set('Driver', 'headless', 'true')
    config_driver = ConfigDriver(config, utils)

    config_driver._create_chrome_options()
    webdriver_mock.ChromeOptions.assert_called_once_with()
    if os.name == 'nt':
        webdriver_mock.ChromeOptions().add_argument.assert_has_calls([mock.call('--headless'),
                                                                      mock.call('--disable-gpu')])
    else:
        webdriver_mock.ChromeOptions().add_argument.assert_called_once_with('--headless')
