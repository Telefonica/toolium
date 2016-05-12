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
import time
import unittest

import mock
import requests_mock
from ddt import ddt, data, unpack
from nose.tools import assert_is_none, assert_equal, assert_raises, assert_in, assert_greater
from requests.exceptions import ConnectionError
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from toolium.config_files import ConfigFiles
from toolium.driver_wrapper import DriverWrapper
from toolium.driver_wrappers_pool import DriverWrappersPool
from toolium.pageelements.page_element import PageElement
from toolium.utils import Utils

navigation_bar_tests = (
    ('android', 'C:/Demo.apk', None, 0),
    ('android', None, 'chrome', 0),
    ('ios', '/tmp/Demo.zip', None, 0),
    ('ios', None, 'safari', 64),
    ('firefox', None, None, 0),
)


def get_mock_element(x, y, height, width):
    """Create a mock element with custom location and size

    :param x: x location
    :param y: y location
    :param height: element height
    :param width: element width
    :returns: mock element
    """
    mock_element = mock.MagicMock(spec=WebElement)
    mock_element.location = {'x': x, 'y': y}
    mock_element.size = {'height': height, 'width': width}
    return mock_element


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

    @requests_mock.Mocker()
    def test_get_remote_node(self, req_mock):
        # Configure mock
        self.driver_wrapper.driver.session_id = '5af'
        url = 'http://{}:{}/grid/api/testsession?session={}'.format('localhost', 4444, '5af')
        grid_response_json = {'session': 'e2', 'proxyId': 'http://10.20.30.40:5555', 'msg': 'slot found !',
                              'inactivityTime': 78, 'success': True, 'internalKey': '7a'}
        req_mock.get(url, json=grid_response_json)

        # Get remote node and check result
        assert_equal(self.utils.get_remote_node(), '10.20.30.40')
        assert_equal(url, req_mock.request_history[0].url)

    @requests_mock.Mocker()
    def test_get_remote_node_non_grid(self, req_mock):
        # Configure mock
        self.driver_wrapper.driver.session_id = '5af'
        url = 'http://{}:{}/grid/api/testsession?session={}'.format('localhost', 4444, '5af')
        req_mock.get(url, text='non_json_response')

        # Get remote node and check result
        assert_equal(self.utils.get_remote_node(), 'localhost')
        assert_equal(url, req_mock.request_history[0].url)

    def test_get_remote_node_local_execution(self):
        self.driver_wrapper.config.set('Server', 'enabled', 'false')
        assert_is_none(self.utils.get_remote_node())

    @requests_mock.Mocker()
    def test_get_remote_video_url(self, req_mock):
        # Configure mock
        url = 'http://{}:{}/video'.format('10.20.30.40', 3000)
        video_url = 'http://{}:{}/download_video/f4.mp4'.format('10.20.30.40', 3000)
        video_response_json = {'exit_code': 1, 'out': [],
                               'error': ['Cannot call this endpoint without required parameters: session and action'],
                               'available_videos': {'5af': {'size': 489701,
                                                            'session': '5af',
                                                            'last_modified': 1460041262558,
                                                            'download_url': video_url,
                                                            'absolute_path': 'C:\\f4.mp4'}},
                               'current_videos': []}
        req_mock.get(url, json=video_response_json)

        # Get remote video url and check result
        assert_equal(self.utils._get_remote_video_url('10.20.30.40', '5af'), video_url)
        assert_equal(url, req_mock.request_history[0].url)

    @requests_mock.Mocker()
    def test_get_remote_video_url_no_videos(self, req_mock):
        # Configure mock
        url = 'http://{}:{}/video'.format('10.20.30.40', 3000)
        video_response_json = {'exit_code': 1, 'out': [],
                               'error': ['Cannot call this endpoint without required parameters: session and action'],
                               'available_videos': {},
                               'current_videos': []}
        req_mock.get(url, json=video_response_json)

        # Get remote video url and check result
        assert_is_none(self.utils._get_remote_video_url('10.20.30.40', '5af'))
        assert_equal(url, req_mock.request_history[0].url)

    @requests_mock.Mocker()
    def test_is_remote_video_enabled(self, req_mock):
        # Configure mock
        url = 'http://{}:{}/config'.format('10.20.30.40', 3000)
        config_response_json = {'out': [], 'error': [], 'exit_code': 0,
                                'filename': ['selenium_grid_extras_config.json'],
                                'config_runtime': {'theConfigMap': {
                                    'video_recording_options': {'width': '1024', 'videos_to_keep': '5',
                                                                'frames': '30',
                                                                'record_test_videos': 'true'}}}}
        req_mock.get(url, json=config_response_json)

        # Get remote video configuration and check result
        assert_equal(self.utils.is_remote_video_enabled('10.20.30.40'), True)
        assert_equal(url, req_mock.request_history[0].url)

    @requests_mock.Mocker()
    def test_is_remote_video_enabled_disabled(self, req_mock):
        # Configure mock
        url = 'http://{}:{}/config'.format('10.20.30.40', 3000)
        config_response_json = {'out': [], 'error': [], 'exit_code': 0,
                                'filename': ['selenium_grid_extras_config.json'],
                                'config_runtime': {'theConfigMap': {
                                    'video_recording_options': {'width': '1024', 'videos_to_keep': '5',
                                                                'frames': '30',
                                                                'record_test_videos': 'false'}}}}
        req_mock.get(url, json=config_response_json)

        # Get remote video configuration and check result
        assert_equal(self.utils.is_remote_video_enabled('10.20.30.40'), False)
        assert_equal(url, req_mock.request_history[0].url)

    @mock.patch('toolium.utils.requests.get')
    def test_is_remote_video_enabled_non_grid_extras(self, req_get_mock):
        # Configure mock
        req_get_mock.side_effect = ConnectionError('exception error')

        # Get remote video configuration and check result
        assert_equal(self.utils.is_remote_video_enabled('10.20.30.40'), False)

    @data(*navigation_bar_tests)
    @unpack
    def test_get_safari_navigation_bar_height(self, driver_type, appium_app, appium_browser_name, bar_height):
        self.driver_wrapper.config.set('Driver', 'type', driver_type)
        if appium_app:
            self.driver_wrapper.config.set('AppiumCapabilities', 'app', appium_app)
        if appium_browser_name:
            self.driver_wrapper.config.set('AppiumCapabilities', 'browserName', appium_browser_name)
        assert_equal(self.utils.get_safari_navigation_bar_height(), bar_height)

    def test_get_window_size_android_native(self):
        # Configure driver mock
        window_size = {'width': 375, 'height': 667}
        self.driver_wrapper.driver.get_window_size.return_value = window_size
        self.driver_wrapper.config.set('Driver', 'type', 'android')
        self.driver_wrapper.config.set('AppiumCapabilities', 'app', 'C:/Demo.apk')

        assert_equal(self.utils.get_window_size(), window_size)
        self.driver_wrapper.driver.get_window_size.assert_called_once_with()

    def test_get_window_size_android_native_two_times(self):
        # Configure driver mock
        window_size = {'width': 375, 'height': 667}
        self.driver_wrapper.driver.get_window_size.return_value = window_size
        self.driver_wrapper.config.set('Driver', 'type', 'android')
        self.driver_wrapper.config.set('AppiumCapabilities', 'app', 'C:/Demo.apk')

        assert_equal(self.utils.get_window_size(), window_size)
        assert_equal(self.utils.get_window_size(), window_size)
        # Check that window size is calculated only one time
        self.driver_wrapper.driver.get_window_size.assert_called_once_with()

    def test_get_window_size_android_web(self):
        # Configure driver mock
        window_size = {'width': 375, 'height': 667}
        self.driver_wrapper.driver.current_context = 'WEBVIEW'
        self.driver_wrapper.driver.execute_script.side_effect = [window_size['width'], window_size['height']]
        self.driver_wrapper.config.set('Driver', 'type', 'android')
        self.driver_wrapper.config.set('AppiumCapabilities', 'browserName', 'chrome')

        assert_equal(self.utils.get_window_size(), window_size)
        self.driver_wrapper.driver.execute_script.assert_has_calls(
            [mock.call('return window.innerWidth'), mock.call('return window.innerHeight')])

    def test_get_window_size_android_web_two_times(self):
        # Configure driver mock
        window_size = {'width': 375, 'height': 667}
        self.driver_wrapper.driver.current_context = 'WEBVIEW'
        self.driver_wrapper.driver.execute_script.side_effect = [window_size['width'], window_size['height']]
        self.driver_wrapper.config.set('Driver', 'type', 'android')
        self.driver_wrapper.config.set('AppiumCapabilities', 'browserName', 'chrome')

        assert_equal(self.utils.get_window_size(), window_size)
        assert_equal(self.utils.get_window_size(), window_size)
        # Check that window size is calculated only one time
        self.driver_wrapper.driver.execute_script.assert_has_calls(
            [mock.call('return window.innerWidth'), mock.call('return window.innerHeight')])

    def test_get_native_coords_android_web(self):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        self.driver_wrapper.driver.current_context = 'WEBVIEW'
        self.driver_wrapper.driver.execute_script.side_effect = [web_window_size['width'], web_window_size['height']]
        self.driver_wrapper.driver.get_window_size.side_effect = [native_window_size]
        self.driver_wrapper.config.set('Driver', 'type', 'android')
        self.driver_wrapper.config.set('AppiumCapabilities', 'browserName', 'chrome')

        web_coords = {'x': 105, 'y': 185}
        native_coords = {'x': 52.5, 'y': 92.5}
        assert_equal(self.utils.get_native_coords(web_coords), native_coords)

    def test_get_native_coords_ios_web(self):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        self.driver_wrapper.driver.get_window_size.side_effect = [web_window_size, native_window_size]
        self.driver_wrapper.config.set('Driver', 'type', 'ios')
        self.driver_wrapper.config.set('AppiumCapabilities', 'browserName', 'safari')

        web_coords = {'x': 105, 'y': 185}
        native_coords = {'x': 52.5, 'y': 156.5}
        assert_equal(self.utils.get_native_coords(web_coords), native_coords)

    def test_swipe_android_native(self):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        self.driver_wrapper.driver.get_window_size.side_effect = [web_window_size, native_window_size]
        self.driver_wrapper.driver.current_context = 'NATIVE_APP'
        self.driver_wrapper.config.set('Driver', 'type', 'android')
        self.driver_wrapper.config.set('AppiumCapabilities', 'app', 'C:/Demo.apk')

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        self.utils.swipe(element, 50, 100)
        self.driver_wrapper.driver.swipe.assert_called_once_with(400, 60, 450, 160, None)

    def test_swipe_android_web(self):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        self.driver_wrapper.driver.current_context = 'WEBVIEW'
        self.driver_wrapper.driver.execute_script.side_effect = [web_window_size['width'], web_window_size['height']]
        self.driver_wrapper.driver.get_window_size.side_effect = [native_window_size]
        self.driver_wrapper.config.set('Driver', 'type', 'android')
        self.driver_wrapper.config.set('AppiumCapabilities', 'browserName', 'chrome')

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        self.utils.swipe(element, 50, 100)
        self.driver_wrapper.driver.swipe.assert_called_once_with(200, 30, 250, 130, None)

    def test_swipe_android_hybrid(self):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        # self.driver_wrapper.utils
        self.driver_wrapper.driver.get_window_size.side_effect = [web_window_size, native_window_size]
        self.driver_wrapper.driver.current_context = 'WEBVIEW'
        self.driver_wrapper.config.set('Driver', 'type', 'android')
        self.driver_wrapper.config.set('AppiumCapabilities', 'app', 'C:/Demo.apk')

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        self.utils.swipe(element, 50, 100)
        self.driver_wrapper.driver.swipe.assert_called_once_with(200, 30, 250, 130, None)

    def test_swipe_ios_web(self):
        # Configure driver mock
        web_window_size = {'width': 500, 'height': 667}
        native_window_size = {'width': 250, 'height': 450}
        self.driver_wrapper.driver.get_window_size.side_effect = [web_window_size, native_window_size]
        self.driver_wrapper.config.set('Driver', 'type', 'ios')
        self.driver_wrapper.config.set('AppiumCapabilities', 'browserName', 'safari')

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        self.utils.swipe(element, 50, 100)
        self.driver_wrapper.driver.swipe.assert_called_once_with(200, 94, 50, 100, None)

    def test_swipe_web(self):
        # Configure driver mock
        self.driver_wrapper.config.set('Driver', 'type', 'firefox')

        # Create element mock
        element = get_mock_element(x=250, y=40, height=40, width=300)

        with assert_raises(Exception) as cm:
            self.utils.swipe(element, 50, 100)
        assert_equal(str(cm.exception), 'Swipe method is not implemented in Selenium')

    def test_get_web_element_from_web_element(self):
        element = WebElement(None, 1)
        web_element = self.utils.get_web_element(element)
        assert_equal(element, web_element)

    def test_get_web_element_from_page_element(self):
        element = PageElement(By.ID, 'element_id')
        element._web_element = 'mock_element'

        web_element = self.utils.get_web_element(element)
        assert_equal('mock_element', web_element)

    def test_get_web_element_from_locator(self):
        # Configure driver mock
        self.driver_wrapper.driver.find_element.return_value = 'mock_element'
        element_locator = (By.ID, 'element_id')

        # Get element and assert response
        web_element = self.utils.get_web_element(element_locator)
        assert_equal('mock_element', web_element)
        self.driver_wrapper.driver.find_element.assert_called_once_with(*element_locator)

    def test_get_web_element_from_none(self):
        web_element = self.utils.get_web_element(None)
        assert_is_none(web_element)

    def test_get_web_element_from_unknown(self):
        web_element = self.utils.get_web_element(dict())
        assert_is_none(web_element)

    def test_wait_until_first_element_is_found_locator(self):
        # Configure driver mock
        self.driver_wrapper.driver.find_element.return_value = 'mock_element'
        element_locator = (By.ID, 'element_id')

        element = self.utils.wait_until_first_element_is_found([element_locator])

        assert_equal(element_locator, element)
        self.driver_wrapper.driver.find_element.assert_called_once_with(*element_locator)

    def test_wait_until_first_element_is_found_page_element(self):
        page_element = PageElement(By.ID, 'element_id')
        page_element._web_element = 'mock_element'

        element = self.utils.wait_until_first_element_is_found([page_element])

        assert_equal(page_element, element)

    def test_wait_until_first_element_is_found_none(self):
        page_element = PageElement(By.ID, 'element_id')
        page_element._web_element = 'mock_element'

        element = self.utils.wait_until_first_element_is_found([None, page_element])

        assert_equal(page_element, element)

    def test_wait_until_first_element_is_found_timeout(self):
        # Configure driver mock
        self.driver_wrapper.driver.find_element.side_effect = NoSuchElementException('Unknown')
        element_locator = (By.ID, 'element_id')

        start_time = time.time()
        with assert_raises(TimeoutException) as cm:
            self.utils.wait_until_first_element_is_found([element_locator], timeout=10)
        end_time = time.time()

        assert_in("None of the page elements has been found after 10 seconds", str(cm.exception))
        # find_element has been called more than one time
        self.driver_wrapper.driver.find_element.assert_called_with(*element_locator)
        assert_greater(end_time - start_time, 10, 'Execution time must be greater than timeout')
