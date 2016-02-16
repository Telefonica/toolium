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

import os
import unittest

import mock
from ddt import ddt, data, unpack
from nose.tools import assert_is_none, assert_equal, assert_raises
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.utils import Utils

navigation_bar_tests = (
    ('android', 'C:/Demo.apk', None, 0),
    ('android', None, 'chrome', 0),
    ('ios', '/tmp/Demo.zip', None, 0),
    ('ios', None, 'safari', 64),
    ('firefox', None, None, 0),
)


@ddt
class UtilsTests(unittest.TestCase):
    def setUp(self):
        # Reset wrappers pool values
        DriverWrappersPool._empty_pool()
        DriverWrapper.config_properties_filenames = None

        # Create a new wrapper
        self.driver_wrapper = DriverWrappersPool.get_default_wrapper()
        self.driver_wrapper.driver = mock.MagicMock()

        # Configure properties
        self.root_path = os.path.dirname(os.path.realpath(__file__))
        config_files = ConfigFiles()
        config_files.set_config_directory(os.path.join(self.root_path, 'conf'))
        config_files.set_config_properties_filenames('properties.cfg')
        config_files.set_output_directory(os.path.join(self.root_path, 'output'))
        self.driver_wrapper.configure(tc_config_files=config_files)

        # Create a new Utils instance
        self.utils = Utils()

    @classmethod
    def tearDownClass(cls):
        # Reset wrappers pool values
        DriverWrappersPool._empty_pool()
        DriverWrapper.config_properties_filenames = None

    @data(*navigation_bar_tests)
    @unpack
    def test_get_safari_navigation_bar_height(self, browser, appium_app, appium_browser_name, bar_height):
        self.driver_wrapper.config.set('Browser', 'browser', browser)
        if appium_app:
            self.driver_wrapper.config.set('AppiumCapabilities', 'app', appium_app)
        if appium_browser_name:
            self.driver_wrapper.config.set('AppiumCapabilities', 'browserName', appium_browser_name)
        assert_equal(self.utils.get_safari_navigation_bar_height(), bar_height)

    def test_get_window_size_android_native(self):
        # Configure driver mock
        window_size = {'width': 375, 'height': 667}
        self.driver_wrapper.driver.get_window_size.return_value = window_size
        self.driver_wrapper.config.set('Browser', 'browser', 'android')
        self.driver_wrapper.config.set('AppiumCapabilities', 'app', 'C:/Demo.apk')

        assert_equal(self.utils.get_window_size(), window_size)

    def test_get_window_size_android_web(self):
        # Configure driver mock
        window_size = {'width': 375, 'height': 667}
        self.driver_wrapper.driver.current_context = 'WEBVIEW'
        self.driver_wrapper.driver.execute_script.side_effect = [window_size['width'], window_size['height']]
        self.driver_wrapper.config.set('Browser', 'browser', 'android')
        self.driver_wrapper.config.set('AppiumCapabilities', 'browserName', 'chrome')

        assert_equal(self.utils.get_window_size(), window_size)

    def test_get_native_coords_android_web(self):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        self.driver_wrapper.driver.current_context = 'WEBVIEW'
        self.driver_wrapper.driver.execute_script.side_effect = [web_window_size['width'], web_window_size['height'],
                                                                 native_window_size['width'],
                                                                 native_window_size['height']]
        self.driver_wrapper.config.set('Browser', 'browser', 'android')
        self.driver_wrapper.config.set('AppiumCapabilities', 'browserName', 'chrome')

        web_coords = {'x': 105, 'y': 185}
        native_coords = {'x': 52.5, 'y': 92.5}
        assert_equal(self.utils.get_native_coords(web_coords), native_coords)

    def test_get_native_coords_ios_web(self):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        self.driver_wrapper.driver.get_window_size.side_effect = [web_window_size, native_window_size]
        self.driver_wrapper.config.set('Browser', 'browser', 'ios')
        self.driver_wrapper.config.set('AppiumCapabilities', 'browserName', 'safari')

        web_coords = {'x': 105, 'y': 185}
        native_coords = {'x': 52.5, 'y': 156.5}
        assert_equal(self.utils.get_native_coords(web_coords), native_coords)

    def test_swipe_android_native(self):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        self.driver_wrapper.driver.current_context = 'NATIVE_APP'
        self.driver_wrapper.driver.get_window_size.side_effect = [web_window_size, native_window_size]
        self.driver_wrapper.config.set('Browser', 'browser', 'android')
        self.driver_wrapper.config.set('AppiumCapabilities', 'app', 'C:/Demo.apk')

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        self.utils.swipe(element, 50, 100)
        self.driver_wrapper.driver.swipe.assert_called_with(400, 60, 450, 160, None)

    def test_swipe_android_web(self):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        self.driver_wrapper.driver.current_context = 'WEBVIEW'
        self.driver_wrapper.driver.execute_script.side_effect = [web_window_size['width'], web_window_size['height'],
                                                                 native_window_size['width'],
                                                                 native_window_size['height']]
        self.driver_wrapper.config.set('Browser', 'browser', 'android')
        self.driver_wrapper.config.set('AppiumCapabilities', 'browserName', 'chrome')

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        self.utils.swipe(element, 50, 100)
        self.driver_wrapper.driver.swipe.assert_called_with(200, 30, 250, 130, None)

    def test_swipe_android_native(self):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        self.driver_wrapper.driver.get_window_size.side_effect = [web_window_size, native_window_size]
        self.driver_wrapper.driver.current_context = 'NATIVE_APP'
        self.driver_wrapper.config.set('Browser', 'browser', 'android')
        self.driver_wrapper.config.set('AppiumCapabilities', 'app', 'C:/Demo.apk')

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        self.utils.swipe(element, 50, 100)
        self.driver_wrapper.driver.swipe.assert_called_with(400, 60, 450, 160, None)

    def test_swipe_android_hybrid(self):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        self.driver_wrapper.driver.get_window_size.side_effect = [web_window_size, native_window_size]
        self.driver_wrapper.driver.current_context = 'WEBVIEW'
        self.driver_wrapper.config.set('Browser', 'browser', 'android')
        self.driver_wrapper.config.set('AppiumCapabilities', 'app', 'C:/Demo.apk')

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        self.utils.swipe(element, 50, 100)
        self.driver_wrapper.driver.swipe.assert_called_with(200, 30, 250, 130, None)

    def test_swipe_ios_web(self):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        self.driver_wrapper.driver.get_window_size.side_effect = [web_window_size, native_window_size]
        self.driver_wrapper.config.set('Browser', 'browser', 'ios')
        self.driver_wrapper.config.set('AppiumCapabilities', 'browserName', 'safari')

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        self.utils.swipe(element, 50, 100)
        self.driver_wrapper.driver.swipe.assert_called_with(200, 94, 250, 194, None)

    def test_swipe_web(self):
        # Configure driver mock
        self.driver_wrapper.config.set('Browser', 'browser', 'firefox')

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        with assert_raises(Exception) as cm:
            self.utils.swipe(element, 50, 100)
        assert_equal(str(cm.exception), 'Swipe method is not implemented in Selenium')

    def test_get_element_none(self):
        element = self.utils.get_element(None)
        assert_is_none(element)

    def test_get_element_webelement(self):
        web_element = WebElement(None, 1)
        element = self.utils.get_element(web_element)
        assert_equal(web_element, element)

    def test_get_element_pageelement(self):
        page_element = mock.MagicMock()
        page_element.element = 'mock_element'

        element = self.utils.get_element(page_element)
        assert_equal('mock_element', element)

    def test_get_element_locator(self):
        # Configure driver mock
        self.driver_wrapper.driver.find_element.return_value = 'mock_element'
        element_locator = (By.ID, 'element_id')

        # Get element and assert response
        element = self.utils.get_element(element_locator)
        assert_equal('mock_element', element)
        self.driver_wrapper.driver.find_element.assert_called_with(*element_locator)


@mock.patch('selenium.webdriver.remote.webelement.WebElement', spec=True)
def get_mock_element(WebElement, x, y, height, width):
    element = WebElement.return_value
    element.location = {'x': x, 'y': y}
    element.size = {'height': height, 'width': width}
    return element
