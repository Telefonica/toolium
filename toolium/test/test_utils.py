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
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from toolium import toolium_wrapper
from toolium.config_files import ConfigFiles
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
        # Remove previous driver instance and conf properties
        toolium_wrapper._instance = None
        toolium_wrapper.config_properties_filenames = None

        # Configure properties
        self.root_path = os.path.dirname(os.path.realpath(__file__))
        config_files = ConfigFiles()
        config_files.set_config_directory(os.path.join(self.root_path, 'conf'))
        config_files.set_config_properties_filenames('properties.cfg')
        config_files.set_output_directory(os.path.join(self.root_path, 'output'))
        toolium_wrapper.configure(tc_config_files=config_files)

        # Create a new Utils instance
        self.utils = Utils()

    @classmethod
    def tearDownClass(cls):
        # Remove driver instance and conf properties
        toolium_wrapper._instance = None
        toolium_wrapper.config_properties_filenames = None

    @data(*navigation_bar_tests)
    @unpack
    def test_get_safari_navigation_bar_height(self, browser, appium_app, appium_browser_name, bar_height):
        toolium_wrapper.config.set('Browser', 'browser', browser)
        if appium_app:
            toolium_wrapper.config.set('AppiumCapabilities', 'app', appium_app)
        if appium_browser_name:
            toolium_wrapper.config.set('AppiumCapabilities', 'browserName', appium_browser_name)
        self.assertEqual(self.utils.get_safari_navigation_bar_height(), bar_height)

    @mock.patch('toolium.toolium_wrapper.driver')
    def test_get_window_size_android_native(self, driver):
        # Configure driver mock
        window_size = {'width': 375, 'height': 667}
        driver.get_window_size.return_value = window_size
        toolium_wrapper.config.set('Browser', 'browser', 'android')
        toolium_wrapper.config.set('AppiumCapabilities', 'app', 'C:/Demo.apk')

        self.assertEqual(self.utils.get_window_size(), window_size)

    @mock.patch('toolium.toolium_wrapper.driver')
    def test_get_window_size_android_web(self, driver):
        # Configure driver mock
        window_size = {'width': 375, 'height': 667}
        driver.current_context = 'WEBVIEW'
        driver.execute_script.side_effect = [window_size['width'], window_size['height']]
        toolium_wrapper.config.set('Browser', 'browser', 'android')
        toolium_wrapper.config.set('AppiumCapabilities', 'browserName', 'chrome')

        self.assertEqual(self.utils.get_window_size(), window_size)

    @mock.patch('toolium.toolium_wrapper.driver')
    def test_get_native_coords_android_web(self, driver):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        driver.current_context = 'WEBVIEW'
        driver.execute_script.side_effect = [web_window_size['width'], web_window_size['height'],
                                             native_window_size['width'], native_window_size['height']]
        toolium_wrapper.config.set('Browser', 'browser', 'android')
        toolium_wrapper.config.set('AppiumCapabilities', 'browserName', 'chrome')

        web_coords = {'x': 105, 'y': 185}
        native_coords = {'x': 52.5, 'y': 92.5}
        self.assertEqual(self.utils.get_native_coords(web_coords), native_coords)

    @mock.patch('toolium.toolium_wrapper.driver')
    def test_get_native_coords_ios_web(self, driver):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        driver.get_window_size.side_effect = [web_window_size, native_window_size]
        toolium_wrapper.config.set('Browser', 'browser', 'ios')
        toolium_wrapper.config.set('AppiumCapabilities', 'browserName', 'safari')

        web_coords = {'x': 105, 'y': 185}
        native_coords = {'x': 52.5, 'y': 156.5}
        self.assertEqual(self.utils.get_native_coords(web_coords), native_coords)

    @mock.patch('toolium.toolium_wrapper.driver')
    def test_swipe_android_native(self, driver):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        driver.current_context = 'NATIVE_APP'
        driver.get_window_size.side_effect = [web_window_size, native_window_size]
        toolium_wrapper.config.set('Browser', 'browser', 'android')
        toolium_wrapper.config.set('AppiumCapabilities', 'app', 'C:/Demo.apk')

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        self.utils.swipe(element, 50, 100)
        driver.swipe.assert_called_with(400, 60, 450, 160, None)

    @mock.patch('toolium.toolium_wrapper.driver')
    def test_swipe_android_web(self, driver):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        driver.current_context = 'WEBVIEW'
        driver.execute_script.side_effect = [web_window_size['width'], web_window_size['height'],
                                             native_window_size['width'], native_window_size['height']]
        toolium_wrapper.config.set('Browser', 'browser', 'android')
        toolium_wrapper.config.set('AppiumCapabilities', 'browserName', 'chrome')

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        self.utils.swipe(element, 50, 100)
        driver.swipe.assert_called_with(200, 30, 250, 130, None)

    @mock.patch('toolium.toolium_wrapper.driver')
    def test_swipe_android_native(self, driver):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        driver.get_window_size.side_effect = [web_window_size, native_window_size]
        driver.current_context = 'NATIVE_APP'
        toolium_wrapper.config.set('Browser', 'browser', 'android')
        toolium_wrapper.config.set('AppiumCapabilities', 'app', 'C:/Demo.apk')

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        self.utils.swipe(element, 50, 100)
        driver.swipe.assert_called_with(400, 60, 450, 160, None)

    @mock.patch('toolium.toolium_wrapper.driver')
    def test_swipe_android_hybrid(self, driver):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        driver.get_window_size.side_effect = [web_window_size, native_window_size]
        driver.current_context = 'WEBVIEW'
        toolium_wrapper.config.set('Browser', 'browser', 'android')
        toolium_wrapper.config.set('AppiumCapabilities', 'app', 'C:/Demo.apk')

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        self.utils.swipe(element, 50, 100)
        driver.swipe.assert_called_with(200, 30, 250, 130, None)

    @mock.patch('toolium.toolium_wrapper.driver')
    def test_swipe_ios_web(self, driver):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        driver.get_window_size.side_effect = [web_window_size, native_window_size]
        toolium_wrapper.config.set('Browser', 'browser', 'ios')
        toolium_wrapper.config.set('AppiumCapabilities', 'browserName', 'safari')

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        self.utils.swipe(element, 50, 100)
        driver.swipe.assert_called_with(200, 94, 250, 194, None)

    @mock.patch('toolium.toolium_wrapper.driver')
    def test_swipe_web(self, driver):
        # Configure driver mock
        toolium_wrapper.config.set('Browser', 'browser', 'firefox')

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        with self.assertRaises(Exception) as cm:
            self.utils.swipe(element, 50, 100)
        self.assertEqual(str(cm.exception), 'Swipe method is not implemented in Selenium')

    def test_get_element_none(self):
        element = self.utils.get_element(None)
        self.assertIsNone(element)

    def test_get_element_webelement(self):
        web_element = WebElement(None, 1)
        element = self.utils.get_element(web_element)
        self.assertEqual(web_element, element)

    def test_get_element_pageelement(self):
        page_element = mock.MagicMock()
        page_element.element.return_value = 'mock_element'

        element = self.utils.get_element(page_element)
        self.assertEqual('mock_element', element)
        page_element.element.assert_called_with()

    @mock.patch('toolium.toolium_wrapper.driver')
    def test_get_element_locator(self, driver):
        # Configure driver mock
        driver.find_element.return_value = 'mock_element'
        element_locator = (By.ID, 'element_id')

        # Get element and assert response
        element = self.utils.get_element(element_locator)
        self.assertEqual('mock_element', element)
        driver.find_element.assert_called_with(*element_locator)


@mock.patch('selenium.webdriver.remote.webelement.WebElement', spec=True)
def get_mock_element(WebElement, x, y, height, width):
    element = WebElement.return_value
    element.location = {'x': x, 'y': y}
    element.size = {'height': height, 'width': width}
    return element
